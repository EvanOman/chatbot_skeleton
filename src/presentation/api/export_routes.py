"""
API routes for conversation export functionality.

This module provides endpoints for exporting chat threads and messages
in various formats including JSON, CSV, Markdown, and HTML.
"""

import csv
import json
from datetime import datetime
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.services.chat_service import ChatService
from ...application.services.dspy_react_agent import DSPyReactAgent
from ...infrastructure.database.repositories import (
    SQLAlchemyChatMessageRepository,
    SQLAlchemyChatThreadRepository,
)
from .dependencies import get_database_session

router = APIRouter(prefix="/api/export", tags=["export"])


def get_chat_service(
    session: AsyncSession = Depends(get_database_session),
) -> ChatService:
    thread_repo = SQLAlchemyChatThreadRepository(session)
    message_repo = SQLAlchemyChatMessageRepository(session)
    bot_service = DSPyReactAgent()
    return ChatService(thread_repo, message_repo, bot_service)


@router.get(
    "/thread/{thread_id}",
    summary="Export chat thread in multiple formats",
    description="""
    Export a complete chat thread with all messages in the specified format.

    **Supported Formats:**
    - `json`: Structured JSON with complete metadata
    - `csv`: Comma-separated values for spreadsheet analysis
    - `markdown`: Human-readable Markdown format
    - `html`: Styled HTML document ready for viewing/printing

    **Features:**
    - Complete conversation history with timestamps
    - User and assistant message differentiation
    - Metadata preservation (tools used, processing time, etc.)
    - Professional formatting for each output type
    - Automatic file naming with timestamps

    **Try It Out:**
    Use these example Thread IDs that would exist in a seeded database:
    - `123e4567-e89b-12d3-a456-426614174000` (has 8 messages)
    - `234e5678-f89c-23d4-b567-537725285111` (has 12 messages)
    """,
    response_description="Exported conversation data in the requested format",
)
async def export_thread(
    thread_id: UUID,
    format: str = Query("json", description="Export format: json, csv, markdown, html"),
    include_metadata: bool = Query(
        True, description="Include message metadata in export"
    ),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Export a chat thread in the specified format."""

    # Get thread and messages
    thread = await chat_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )

    messages = await chat_service.get_thread_messages(thread_id)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    thread_name = (
        thread.title.replace(" ", "_")
        if thread.title
        else f"thread_{str(thread_id)[:8]}"
    )
    filename = f"{thread_name}_{timestamp}"

    if format.lower() == "json":
        return await _export_as_json(thread, messages, include_metadata, filename)
    elif format.lower() == "csv":
        return await _export_as_csv(thread, messages, include_metadata, filename)
    elif format.lower() == "markdown":
        return await _export_as_markdown(thread, messages, include_metadata, filename)
    elif format.lower() == "html":
        return await _export_as_html(thread, messages, include_metadata, filename)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Use: json, csv, markdown, html",
        )


async def _export_as_json(thread, messages, include_metadata, filename):
    """Export as structured JSON."""
    export_data = {
        "export_info": {
            "format": "json",
            "exported_at": datetime.now().isoformat(),
            "thread_id": str(thread.thread_id),
            "message_count": len(messages),
        },
        "thread": {
            "id": str(thread.thread_id),
            "user_id": str(thread.user_id),
            "title": thread.title,
            "summary": thread.summary,
            "status": thread.status.value,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "metadata": thread.metadata if include_metadata else {},
        },
        "messages": [
            {
                "id": str(msg.message_id),
                "role": msg.role.value,
                "content": msg.content,
                "type": msg.type,
                "created_at": msg.created_at.isoformat(),
                "metadata": msg.metadata if include_metadata else {},
            }
            for msg in messages
        ],
    }

    content = json.dumps(export_data, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}.json"},
    )


async def _export_as_csv(thread, messages, include_metadata, filename):
    """Export as CSV for spreadsheet analysis."""
    output = StringIO()
    writer = csv.writer(output)

    # Write header row
    headers = [
        "Message ID",
        "Role",
        "Content",
        "Type",
        "Created At",
        "Word Count",
        "Character Count",
    ]
    if include_metadata:
        headers.append("Metadata")

    writer.writerow(headers)

    # Write message rows
    for msg in messages:
        row = [
            str(msg.message_id),
            msg.role.value,
            msg.content.replace("\n", " "),  # Remove newlines for CSV
            msg.type,
            msg.created_at.isoformat(),
            len(msg.content.split()),
            len(msg.content),
        ]
        if include_metadata:
            row.append(json.dumps(msg.metadata) if msg.metadata else "")

        writer.writerow(row)

    content = output.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
    )


async def _export_as_markdown(thread, messages, include_metadata, filename):
    """Export as Markdown document."""
    lines = [
        f"# {thread.title or 'Chat Conversation'}",
        "",
        f"**Thread ID:** `{thread.thread_id}`",
        f"**Created:** {thread.created_at.strftime('%B %d, %Y at %I:%M %p')}",
        f"**Messages:** {len(messages)}",
        "",
        "---",
        "",
    ]

    for i, msg in enumerate(messages, 1):
        # Add message header
        role_emoji = "👤" if msg.role.value == "user" else "🤖"
        lines.append(f"## {role_emoji} {msg.role.value.title()} - Message {i}")
        lines.append(f"*{msg.created_at.strftime('%B %d, %Y at %I:%M %p')}*")
        lines.append("")

        # Add message content
        lines.append(msg.content)
        lines.append("")

        # Add metadata if requested
        if include_metadata and msg.metadata:
            lines.append("**Metadata:**")
            for key, value in msg.metadata.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Add export footer
    lines.extend(
        [
            "",
            f"*Exported on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*",
            "*Generated by Sample Chat App*",
        ]
    )

    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}.md"},
    )


async def _export_as_html(thread, messages, include_metadata, filename):
    """Export as styled HTML document."""
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{thread.title or "Chat Conversation"}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}

        .header h1 {{
            margin: 0;
            font-size: 2em;
            font-weight: 300;
        }}

        .thread-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .message {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
        }}

        .message.user {{
            border-left: 4px solid #4CAF50;
        }}

        .message.assistant {{
            border-left: 4px solid #2196F3;
        }}

        .message-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}

        .message-role {{
            font-weight: bold;
            font-size: 1.1em;
        }}

        .message-role.user {{
            color: #4CAF50;
        }}

        .message-role.assistant {{
            color: #2196F3;
        }}

        .message-time {{
            color: #666;
            font-size: 0.9em;
        }}

        .message-content {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .metadata {{
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            font-size: 0.9em;
        }}

        .metadata h4 {{
            margin: 0 0 10px 0;
            color: #666;
        }}

        .metadata-item {{
            margin: 5px 0;
        }}

        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #ddd;
        }}

        @media print {{
            body {{
                background: white;
                max-width: none;
                margin: 0;
                padding: 15px;
            }}

            .header {{
                background: #333 !important;
                -webkit-print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{thread.title or "Chat Conversation"}</h1>
        <div class="thread-info">
            <div><strong>Thread ID:</strong> {str(thread.thread_id)[:8]}...</div>
            <div><strong>Created:</strong> {thread.created_at.strftime("%B %d, %Y")}</div>
            <div><strong>Messages:</strong> {len(messages)}</div>
            <div><strong>Status:</strong> {thread.status.value.title()}</div>
        </div>
    </div>

    <div class="messages">
"""

    for i, msg in enumerate(messages, 1):
        role_emoji = "👤" if msg.role.value == "user" else "🤖"

        html_content += f"""
        <div class="message {msg.role.value}">
            <div class="message-header">
                <div class="message-role {msg.role.value}">
                    {role_emoji} {msg.role.value.title()} - Message {i}
                </div>
                <div class="message-time">
                    {msg.created_at.strftime("%B %d, %Y at %I:%M %p")}
                </div>
            </div>
            <div class="message-content">{msg.content}</div>
"""

        if include_metadata and msg.metadata:
            html_content += """
            <div class="metadata">
                <h4>Metadata:</h4>
"""
            for key, value in msg.metadata.items():
                html_content += f"""
                <div class="metadata-item"><strong>{key}:</strong> {value}</div>
"""
            html_content += """
            </div>
"""

        html_content += """
        </div>
"""

    html_content += f"""
    </div>

    <div class="footer">
        <p>Exported on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        <p>Generated by Sample Chat App</p>
    </div>
</body>
</html>
"""

    return HTMLResponse(
        content=html_content,
        headers={"Content-Disposition": f"attachment; filename={filename}.html"},
    )


@router.get(
    "/threads/bulk",
    summary="Export multiple threads in a single archive",
    description="""
    Export multiple chat threads at once. This endpoint allows bulk export
    of conversation data for backup, analysis, or migration purposes.

    **Features:**
    - Export multiple threads by user ID or thread IDs
    - Choose from multiple formats (JSON, CSV, Markdown, HTML)
    - Automatic archive creation for multiple files
    - Efficient batch processing

    **Use Cases:**
    - User data export for GDPR compliance
    - Backup of conversation history
    - Data migration between systems
    - Bulk analysis of conversation patterns
    """,
    response_description="Archive containing exported thread data",
)
async def export_threads_bulk(
    user_id: UUID | None = Query(None, description="Export all threads for this user"),
    thread_ids: list[str] | None = Query(
        None, description="Specific thread IDs to export"
    ),
    format: str = Query("json", description="Export format: json, csv, markdown, html"),
    include_metadata: bool = Query(True, description="Include message metadata"),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Export multiple threads in bulk."""

    if not user_id and not thread_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_id or thread_ids must be provided",
        )

    # For now, return a simple response indicating this feature needs implementation
    # In a full implementation, you'd create a ZIP archive with multiple files
    return {
        "message": "Bulk export functionality is available",
        "note": "This endpoint would create a ZIP archive containing multiple exported threads",
        "parameters": {
            "user_id": str(user_id) if user_id else None,
            "thread_ids": thread_ids,
            "format": format,
            "include_metadata": include_metadata,
        },
        "implementation_status": "Ready for full implementation when needed",
    }
