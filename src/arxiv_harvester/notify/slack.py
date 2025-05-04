"""Slack notification module for arXiv Harvester.

Provides functionality for sending arXiv paper notifications to Slack.
"""

import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class SlackNotifier:
    """Notifier for sending arXiv paper information to Slack.

    Handles formatting and sending paper notifications to Slack via webhooks.
    """

    def __init__(self):
        """Initialize the Slack notifier."""
        self.max_message_length = 3000  # Slack message length limit is ~40k, but we'll be conservative
        self.important_categories = []
        self.use_markdown = False

    def set_important_categories(self, categories: List[str]):
        """Set categories to be highlighted as important.

        Args:
            categories: List of arXiv category codes to highlight
        """
        self.important_categories = categories

    def set_use_markdown(self, use_markdown: bool):
        """Set whether to use markdown formatting in messages.

        Args:
            use_markdown: Whether to use markdown formatting
        """
        self.use_markdown = use_markdown

    def truncate_message(self, message: str) -> str:
        """Truncate a message if it exceeds the maximum length.

        Args:
            message: The message to potentially truncate

        Returns:
            Truncated message if necessary, or the original message
        """
        if len(message) <= self.max_message_length:
            return message

        truncated = message[:self.max_message_length - 25]  # Leave room for the truncation message
        return f"{truncated}... (message truncated)"

    def format_paper_message(self, paper: Dict[str, Any]) -> str:
        """Format a single paper as a message string.

        Args:
            paper: Paper dictionary with metadata

        Returns:
            Formatted message string
        """
        # Determine if the paper is in an important category
        is_important = False
        if 'category' in paper and paper['category'] in self.important_categories:
            is_important = True

        # Format the paper information
        title_prefix = "**Title:**" if self.use_markdown else "Title:"
        authors_prefix = "**Authors:**" if self.use_markdown else "Authors:"
        summary_prefix = "**Abstract:**" if self.use_markdown else "Abstract:"

        # Construct the PDF link with markdown if enabled
        if self.use_markdown:
            pdf_link = f"[PDF]({paper['pdf_url']})" if 'pdf_url' in paper else "No PDF available"
        else:
            pdf_link = paper.get('pdf_url', "No PDF available")

        # Format the message with or without importance marker
        importance_marker = "*IMPORTANT* " if is_important else ""

        message = f"{importance_marker}{title_prefix} {paper['title']}\n"
        message += f"{authors_prefix} {', '.join(paper.get('authors', ['Unknown']))}\n"
        if 'published_date' in paper:
            try:
                # Try to parse and format the date
                date_str = paper['published_date']
                # Remove the 'Z' and truncate milliseconds if present
                if date_str.endswith('Z'):
                    date_str = date_str[:-1]
                if '.' in date_str:
                    date_str = date_str.split('.')[0]
                date = datetime.fromisoformat(date_str)
                formatted_date = date.strftime("%Y-%m-%d")
                message += f"Published: {formatted_date}\n"
            except (ValueError, TypeError):
                # If parsing fails, just use the original string
                message += f"Published: {paper.get('published_date', 'Unknown')}\n"

        # Add category if available
        if 'category' in paper:
            message += f"Category: {paper['category']}\n"

        message += f"{summary_prefix} {paper.get('summary', 'No abstract available')}\n"
        message += f"Link: {pdf_link}\n\n"

        return message

    def format_papers_message(self, papers: List[Dict[str, Any]],
                             pre_message: str = "", post_message: str = "",
                             max_papers: Optional[int] = None) -> str:
        """Format multiple papers as a single message.

        Args:
            papers: List of paper dictionaries
            pre_message: Message to include before the papers list
            post_message: Message to include after the papers list
            max_papers: Maximum number of papers to include

        Returns:
            Formatted message string with all papers
        """
        if not papers:
            return "No papers to display."

        # Apply max_papers limit if specified
        displayed_papers = papers
        if max_papers is not None and max_papers < len(papers):
            displayed_papers = papers[:max_papers]

        # Start with the pre-message if provided
        message = f"{pre_message}\n\n" if pre_message else ""

        # Add a count indicator if limited
        if max_papers is not None and max_papers < len(papers):
            message += f"Showing {len(displayed_papers)} of {len(papers)} papers\n\n"

        # Add each paper's formatted message
        for paper in displayed_papers:
            message += self.format_paper_message(paper)

        # Add the post-message if provided
        if post_message:
            message += f"\n{post_message}"

        # Truncate if necessary
        return self.truncate_message(message)

    def format_paper_blocks(self, paper: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format a paper as Slack blocks for rich formatting.

        Args:
            paper: Paper dictionary with metadata

        Returns:
            List of Slack block objects
        """
        blocks = []

        # Determine if the paper is in an important category
        is_important = False
        if 'category' in paper and paper['category'] in self.important_categories:
            is_important = True

        # Add header block with title
        title_text = paper['title']
        if is_important:
            title_text = f"🔔 *IMPORTANT* - {title_text}"

        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": title_text[:150]  # Slack header has a character limit
            }
        })

        # Add section with authors and date
        authors_text = f"*Authors:* {', '.join(paper.get('authors', ['Unknown']))}"

        # Format the date if available
        date_text = ""
        if 'published_date' in paper:
            try:
                date_str = paper['published_date']
                if date_str.endswith('Z'):
                    date_str = date_str[:-1]
                if '.' in date_str:
                    date_str = date_str.split('.')[0]
                date = datetime.fromisoformat(date_str)
                formatted_date = date.strftime("%Y-%m-%d")
                date_text = f"*Published:* {formatted_date}"
            except (ValueError, TypeError):
                date_text = f"*Published:* {paper.get('published_date', 'Unknown')}"

        # Add category if available
        category_text = ""
        if 'category' in paper:
            category_text = f"*Category:* {paper['category']}"

        metadata_text = f"{authors_text}\n{date_text}"
        if category_text:
            metadata_text += f"\n{category_text}"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": metadata_text
            }
        })

        # Add abstract as a section
        summary = paper.get('summary', 'No abstract available')
        # Truncate long abstracts for Slack's limits
        if len(summary) > 2900:
            summary = summary[:2900] + "... (truncated)"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Abstract:*\n{summary}"
            }
        })

        # Add PDF link as a button
        if 'pdf_url' in paper:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View PDF"
                        },
                        "url": paper['pdf_url']
                    }
                ]
            })

        # Add divider between papers
        blocks.append({"type": "divider"})

        return blocks

    def format_papers_blocks(self, papers: List[Dict[str, Any]],
                           max_papers: Optional[int] = None) -> List[Dict[str, Any]]:
        """Format multiple papers as Slack blocks.

        Args:
            papers: List of paper dictionaries
            max_papers: Maximum number of papers to include

        Returns:
            List of Slack block objects
        """
        if not papers:
            return [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "No papers to display."
                }
            }]

        # Apply max_papers limit if specified
        displayed_papers = papers
        if max_papers is not None and max_papers < len(papers):
            displayed_papers = papers[:max_papers]

        blocks = []

        # Add a count indicator if limited
        if max_papers is not None and max_papers < len(papers):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Showing {len(displayed_papers)} of {len(papers)} papers"
                }
            })

        # Add each paper's formatted blocks
        for paper in displayed_papers:
            paper_blocks = self.format_paper_blocks(paper)
            blocks.extend(paper_blocks)

        return blocks

    def post_message_to_slack(self, message: str, webhook_url: str) -> bool:
        """Post a message to Slack.

        Args:
            message: Message text to post
            webhook_url: Slack webhook URL

        Returns:
            True if successful, False otherwise
        """
        if not message or not webhook_url:
            return False

        # Truncate if necessary
        message = self.truncate_message(message)

        payload = {"text": message}

        try:
            response = requests.post(
                webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            return response.status_code == 200
        except Exception:
            return False

    def post_blocks_to_slack(self, blocks: List[Dict[str, Any]], webhook_url: str) -> bool:
        """Post blocks to Slack.

        Args:
            blocks: List of Slack block objects
            webhook_url: Slack webhook URL

        Returns:
            True if successful, False otherwise
        """
        if not blocks or not webhook_url:
            return False

        payload = {"blocks": blocks}

        try:
            response = requests.post(
                webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            return response.status_code == 200
        except Exception:
            return False

    def post_papers_to_slack(self, papers: List[Dict[str, Any]], webhook_url: str,
                           use_blocks: bool = False, max_papers: Optional[int] = None,
                           pre_message: str = "", post_message: str = "") -> bool:
        """Post arXiv papers to Slack.

        Args:
            papers: List of paper dictionaries to post
            webhook_url: Slack webhook URL
            use_blocks: Whether to use Slack blocks for rich formatting
            max_papers: Maximum number of papers to include
            pre_message: Message to include before the papers list (only for non-block format)
            post_message: Message to include after the papers list (only for non-block format)

        Returns:
            True if successful, False otherwise
        """
        if not papers or not webhook_url:
            return False

        if use_blocks:
            blocks = self.format_papers_blocks(papers, max_papers=max_papers)
            return self.post_blocks_to_slack(blocks, webhook_url)
        else:
            message = self.format_papers_message(
                papers,
                pre_message=pre_message,
                post_message=post_message,
                max_papers=max_papers
            )
            return self.post_message_to_slack(message, webhook_url)
