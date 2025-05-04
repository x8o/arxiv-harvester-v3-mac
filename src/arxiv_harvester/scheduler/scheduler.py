"""Scheduler module for arXiv Harvester.

Provides functionality for scheduling and running the arXiv harvesting process.
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any


class Scheduler:
    """Scheduler for automating the arXiv paper harvesting process.

    Handles scheduling, fetching, storing, and notifying about new arXiv papers.
    """

    def __init__(self, api_client, db_manager, notifier):
        """Initialize the scheduler.

        Args:
            api_client: ArxivApiClient instance for fetching papers
            db_manager: DatabaseManager instance for storing papers
            notifier: SlackNotifier instance for sending notifications
        """
        self.api_client = api_client
        self.db_manager = db_manager
        self.notifier = notifier

        # Search parameters
        self.query = ''
        self.categories = []
        self.max_results = 50

        # Notification parameters
        self.slack_webhook = None

        # Scheduling parameters
        self.schedule_type = "weekly"  # Default to weekly
        self.last_run_time = None

        # State management
        self.state_file = None

    def set_search_parameters(
        self, query: str, categories: List[str] = None, max_results: int = 50
    ) -> None:
        """Set the search parameters for API queries.

        Args:
            query: Search query string
            categories: List of arXiv categories to search in
            max_results: Maximum number of results to fetch per category
        """
        self.query = query
        self.categories = categories or []
        self.max_results = max_results

    def set_slack_webhook(self, webhook_url: str):
        """Set the Slack webhook URL for notifications.

        Args:
            webhook_url: Slack webhook URL
        """
        self.slack_webhook = webhook_url

    def set_schedule(self, schedule_type: str):
        """Set the schedule type for harvesting.

        Args:
            schedule_type: Type of schedule ('daily', 'weekly', 'monthly')
        """
        self.schedule_type = schedule_type

    def set_last_run_time(self, run_time: datetime):
        """Set the last time the harvester was run.

        Args:
            run_time: Datetime of the last run
        """
        self.last_run_time = run_time

    def set_state_file(self, state_file: str):
        """Set the path to the state file.

        Args:
            state_file: Path to the state file
        """
        self.state_file = state_file

    def fetch_papers(self) -> List[Dict[str, Any]]:
        """Fetch papers from the arXiv API based on set parameters.

        Returns:
            List of paper dictionaries

        Raises:
            Exception: If there's an error during the API request
        """
        try:
            all_papers = []

            # If categories are specified, search each category separately
            if self.categories:
                for category in self.categories:
                    papers = self.api_client.search(
                        query=self.query,
                        category=category,
                        max_results=self.max_results
                    )
                    all_papers.extend(papers)
            else:
                # Search without category
                all_papers = self.api_client.search(
                    query=self.query,
                    max_results=self.max_results
                )

            return all_papers

        except Exception as e:
            raise Exception(f"Error fetching papers: {str(e)}")

    def filter_new_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out papers that are already in the database.

        Args:
            papers: List of papers to filter

        Returns:
            List of papers that are not already in the database
        """
        new_papers = []

        for paper in papers:
            # Extract arXiv ID from the full URL
            full_id = paper['id']
            arxiv_id = full_id.split('/')[-1] if '/' in full_id else full_id

            # Check if paper exists in database
            existing_paper = self.db_manager.get_paper_by_id(arxiv_id)

            if existing_paper is None:
                new_papers.append(paper)

        return new_papers

    def store_papers(self, papers: List[Dict[str, Any]]):
        """Store papers in the database.

        Args:
            papers: List of papers to store
        """
        self.db_manager.store_papers(papers)

    def send_notifications(self, papers: List[Dict[str, Any]]) -> bool:
        """Send notifications about new papers.

        Args:
            papers: List of papers to notify about

        Returns:
            True if notification was successful, False otherwise
        """
        if not papers or not self.slack_webhook:
            return False

        return self.notifier.post_papers_to_slack(
            papers,
            self.slack_webhook,
            use_blocks=True,
            pre_message="New arXiv papers matching your criteria:"
        )

    def is_time_to_run(self) -> bool:
        """Check if it's time to run the harvester based on the schedule.

        Returns:
            True if it's time to run, False otherwise
        """
        # If no last run time, always run
        if self.last_run_time is None:
            return True

        now = datetime.now()

        # Calculate time interval based on schedule type
        if self.schedule_type == "daily":
            interval = timedelta(days=1)
        elif self.schedule_type == "weekly":
            interval = timedelta(days=7)
        elif self.schedule_type == "monthly":
            # Approximate a month as 30 days
            interval = timedelta(days=30)
        else:
            # Default to weekly
            interval = timedelta(days=7)

        # Check if the interval has passed
        return (now - self.last_run_time) >= interval

    def save_state(self, state_file: str = None):
        """Save the current state to a file.

        Args:
            state_file: Path to save the state to, defaults to self.state_file
        """
        target_file = state_file or self.state_file
        if not target_file:
            return

        # Create state dictionary
        state = {
            "query": self.query,
            "categories": self.categories,
            "max_results": self.max_results,
            "slack_webhook": self.slack_webhook,
            "schedule_type": self.schedule_type,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)

        # Write state to file
        with open(target_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, state_file: str = None):
        """Load state from a file.

        Args:
            state_file: Path to load state from, defaults to self.state_file
        """
        target_file = state_file or self.state_file
        if not target_file or not os.path.exists(target_file):
            return

        try:
            # Read state from file
            with open(target_file, 'r') as f:
                state = json.load(f)

            # Apply state
            self.query = state.get("query", "")
            self.categories = state.get("categories", [])
            self.max_results = state.get("max_results", 50)
            self.slack_webhook = state.get("slack_webhook")
            self.schedule_type = state.get("schedule_type", "weekly")

            # Parse last_run_time
            last_run_str = state.get("last_run_time")
            if last_run_str:
                self.last_run_time = datetime.fromisoformat(last_run_str)
            else:
                self.last_run_time = None

        except Exception as e:
            print(f"Error loading state: {str(e)}")

    def parse_arguments(self, args=None):
        """Parse command-line arguments.

        Args:
            args: Command-line arguments (defaults to None, which uses sys.argv)

        Returns:
            Parsed arguments object
        """
        parser = argparse.ArgumentParser(description="arXiv Harvester Scheduler")

        parser.add_argument("--query", type=str, help="Search query")
        parser.add_argument("--categories", type=str, help="Comma-separated list of categories")
        parser.add_argument("--max-results", type=int, help="Maximum number of results per category")
        parser.add_argument("--webhook", type=str, help="Slack webhook URL")
        parser.add_argument("--state-file", type=str, help="Path to state file")
        parser.add_argument("--schedule", type=str, choices=["daily", "weekly", "monthly"],
                           help="Schedule type")
        parser.add_argument("--force-run", action="store_true",
                           help="Run regardless of schedule")

        return parser.parse_args(args)

    def apply_arguments(self, args):
        """Apply parsed arguments to the scheduler.

        Args:
            args: Parsed arguments object
        """
        # Apply search parameters if provided
        if args.query:
            categories = args.categories.split(",") if args.categories else []
            max_results = args.max_results if args.max_results is not None else self.max_results
            self.set_search_parameters(args.query, categories, max_results)

        # Apply webhook if provided
        if args.webhook:
            self.set_slack_webhook(args.webhook)

        # Apply state file if provided
        if args.state_file:
            self.set_state_file(args.state_file)
            self.load_state()

        # Apply schedule if provided
        if args.schedule:
            self.set_schedule(args.schedule)

    def run_harvest(self) -> bool:
        """Run the complete harvesting process.

        Returns:
            True if the process completed, False on critical error
        """
        try:
            # Update last run time
            self.set_last_run_time(datetime.now())

            # Fetch papers
            papers = self.fetch_papers()

            # Filter for new papers
            new_papers = self.filter_new_papers(papers)

            # If there are new papers, store and notify
            if new_papers:
                self.store_papers(new_papers)
                self.send_notifications(new_papers)

            # Save state if state file is set
            if self.state_file:
                self.save_state(self.state_file)

            return True

        except Exception as e:
            print(f"Error during harvest: {str(e)}")
            return False

    def main(self):
        """Main entry point for the scheduler command-line interface."""
        # Parse arguments
        args = self.parse_arguments()

        # Apply arguments and load state
        self.apply_arguments(args)

        # Check if we should run
        should_run = args.force_run or self.is_time_to_run()

        if should_run:
            self.run_harvest()
