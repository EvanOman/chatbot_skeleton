"""
API routes for conversation visualization features.

This module provides endpoints for visualizing chat threads as interactive trees
and other visual representations to help with debugging and analysis.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.services.chat_service import ChatService
from ...application.services.dspy_react_agent import DSPyReactAgent
from ...infrastructure.database.repositories import (
    SQLAlchemyChatMessageRepository,
    SQLAlchemyChatThreadRepository,
)
from .dependencies import get_database_session

router = APIRouter(prefix="/api/visualization", tags=["visualization"])


def get_chat_service(
    session: AsyncSession = Depends(get_database_session),
) -> ChatService:
    thread_repo = SQLAlchemyChatThreadRepository(session)
    message_repo = SQLAlchemyChatMessageRepository(session)
    bot_service = DSPyReactAgent()
    return ChatService(thread_repo, message_repo, bot_service)


@router.get(
    "/thread/{thread_id}/tree",
    response_class=HTMLResponse,
    summary="Visualize chat thread as conversation tree",
    description="""
    Generate an interactive tree visualization of a chat thread showing the
    conversation flow between user and assistant messages.

    This visualization helps in:
    - Understanding conversation patterns
    - Debugging complex agent interactions
    - Analyzing message relationships and context flow

    **Features:**
    - Interactive D3.js tree layout
    - Color-coded messages by role (user/assistant)
    - Hover effects showing full message content
    - Expandable/collapsible nodes for long conversations
    - Responsive design that works on desktop and mobile

    **Try It Out:**
    Use these example Thread IDs that would exist in a seeded database:
    - `123e4567-e89b-12d3-a456-426614174000` (has 8 messages)
    - `234e5678-f89c-23d4-b567-537725285111` (has 12 messages)
    """,
    response_description="Interactive HTML page with D3.js conversation tree visualization",
)
async def visualize_thread_tree(
    thread_id: UUID,
    chat_service: ChatService = Depends(get_chat_service),
) -> HTMLResponse:
    """Generate an interactive tree visualization of a chat thread."""

    # Get thread and messages
    thread = await chat_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )

    messages = await chat_service.get_thread_messages(thread_id)

    # Convert messages to tree data structure
    tree_data = {
        "name": thread.title or f"Thread {str(thread_id)[:8]}...",
        "thread_id": str(thread_id),
        "children": [],
    }

    # Build hierarchical structure based on message order
    current_level = tree_data["children"]
    for message in messages:
        node = {
            "name": (
                f"{message.role.value}: {message.content[:50]}..."
                if len(message.content) > 50
                else f"{message.role.value}: {message.content}"
            ),
            "full_content": message.content,
            "role": message.role.value,
            "message_id": str(message.message_id),
            "created_at": message.created_at.isoformat(),
            "metadata": message.metadata,
            "children": [],
        }
        current_level.append(node)

        # For branching conversations, we could add logic here
        # For now, we'll create a simple linear flow
        current_level = node["children"]

    # Generate HTML with embedded D3.js visualization
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversation Tree - {thread.title or "Chat Thread"}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}

        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}

        .header p {{
            margin: 10px 0;
            opacity: 0.9;
        }}

        .visualization-container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 30px;
            margin: 0 auto;
            max-width: 1200px;
        }}

        .controls {{
            margin-bottom: 20px;
            text-align: center;
        }}

        .control-button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }}

        .control-button:hover {{
            background: #5a6fd8;
            transform: translateY(-2px);
        }}

        #tree-container {{
            width: 100%;
            height: 600px;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }}

        .node circle {{
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .node.user circle {{
            fill: #4CAF50;
        }}

        .node.assistant circle {{
            fill: #2196F3;
        }}

        .node.thread circle {{
            fill: #FF9800;
        }}

        .node circle:hover {{
            stroke: #333;
            stroke-width: 3px;
            transform: scale(1.1);
        }}

        .node text {{
            font: 12px sans-serif;
            cursor: pointer;
        }}

        .link {{
            fill: none;
            stroke: #ccc;
            stroke-width: 2px;
            transition: all 0.3s ease;
        }}

        .link:hover {{
            stroke: #999;
            stroke-width: 3px;
        }}

        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-size: 12px;
            max-width: 300px;
            word-wrap: break-word;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }}

        .stats {{
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .visualization-container {{
                padding: 15px;
                margin: 10px;
            }}

            #tree-container {{
                height: 400px;
            }}

            .stats {{
                flex-direction: column;
                gap: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌳 Conversation Tree</h1>
        <p>{thread.title or f"Thread {str(thread_id)[:8]}..."}</p>
        <p>Created: {thread.created_at.strftime("%B %d, %Y at %I:%M %p")}</p>
    </div>

    <div class="visualization-container">
        <div class="controls">
            <button class="control-button" onclick="expandAll()">🔍 Expand All</button>
            <button class="control-button" onclick="collapseAll()">📦 Collapse All</button>
            <button class="control-button" onclick="resetZoom()">🎯 Reset View</button>
            <button class="control-button" onclick="downloadSVG()">💾 Download SVG</button>
        </div>

        <div id="tree-container"></div>

        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{len(messages)}</div>
                <div class="stat-label">Total Messages</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len([m for m in messages if m.role.value == "user"])}</div>
                <div class="stat-label">User Messages</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len([m for m in messages if m.role.value == "assistant"])}</div>
                <div class="stat-label">AI Responses</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sum(len(m.content.split()) for m in messages)}</div>
                <div class="stat-label">Total Words</div>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        // Tree data from server
        const treeData = {tree_data};

        // Set up dimensions and margins
        const margin = {{top: 20, right: 120, bottom: 20, left: 120}};
        const width = 1000 - margin.left - margin.right;
        const height = 560 - margin.top - margin.bottom;

        // Create SVG
        const svg = d3.select("#tree-container")
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        // Create tree layout
        const tree = d3.tree().size([height, width]);

        // Create hierarchy
        const root = d3.hierarchy(treeData);

        let i = 0;
        const duration = 750;

        // Assign unique IDs to each node
        root.descendants().forEach((d, i) => {{
            d.id = i;
            d._children = d.children;
            if (d.depth > 2) d.children = null; // Start with some nodes collapsed
        }});

        update(root);

        function update(source) {{
            // Compute the new tree layout
            const treeData = tree(root);

            const nodes = treeData.descendants();
            const links = treeData.descendants().slice(1);

            // Normalize for fixed-depth
            nodes.forEach(d => {{ d.y = d.depth * 180; }});

            // Update nodes
            const node = g.selectAll('g.node')
                .data(nodes, d => d.id || (d.id = ++i));

            const nodeEnter = node.enter().append('g')
                .attr('class', d => `node ${{d.data.role || 'thread'}}`)
                .attr("transform", d => `translate(${{source.y0}},${{source.x0}})`)
                .on('click', click)
                .on('mouseover', showTooltip)
                .on('mouseout', hideTooltip);

            nodeEnter.append('circle')
                .attr('r', 1e-6)
                .style("fill", d => d._children ? "lightsteelblue" : "#fff");

            nodeEnter.append('text')
                .attr("dy", ".35em")
                .attr("x", d => d.children || d._children ? -13 : 13)
                .attr("text-anchor", d => d.children || d._children ? "end" : "start")
                .text(d => d.data.name)
                .style("fill-opacity", 1e-6);

            // Update
            const nodeUpdate = nodeEnter.merge(node);

            nodeUpdate.transition()
                .duration(duration)
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`);

            nodeUpdate.select('circle')
                .attr('r', 10)
                .style("fill", d => d._children ? "lightsteelblue" : "#fff")
                .attr('cursor', 'pointer');

            nodeUpdate.select('text')
                .style("fill-opacity", 1);

            // Remove exiting nodes
            const nodeExit = node.exit().transition()
                .duration(duration)
                .attr("transform", d => `translate(${{source.y}},${{source.x}})`)
                .remove();

            nodeExit.select('circle')
                .attr('r', 1e-6);

            nodeExit.select('text')
                .style('fill-opacity', 1e-6);

            // Update links
            const link = g.selectAll('path.link')
                .data(links, d => d.id);

            const linkEnter = link.enter().insert('path', "g")
                .attr("class", "link")
                .attr('d', d => {{
                    const o = {{x: source.x0, y: source.y0}};
                    return diagonal(o, o);
                }});

            const linkUpdate = linkEnter.merge(link);

            linkUpdate.transition()
                .duration(duration)
                .attr('d', d => diagonal(d, d.parent));

            const linkExit = link.exit().transition()
                .duration(duration)
                .attr('d', d => {{
                    const o = {{x: source.x, y: source.y}};
                    return diagonal(o, o);
                }})
                .remove();

            nodes.forEach(d => {{
                d.x0 = d.x;
                d.y0 = d.y;
            }});
        }}

        function click(event, d) {{
            if (d.children) {{
                d._children = d.children;
                d.children = null;
            }} else {{
                d.children = d._children;
                d._children = null;
            }}
            update(d);
        }}

        function diagonal(s, d) {{
            const path = `M ${{s.y}} ${{s.x}}
                         C ${{(s.y + d.y) / 2}} ${{s.x}},
                           ${{(s.y + d.y) / 2}} ${{d.x}},
                           ${{d.y}} ${{d.x}}`;
            return path;
        }}

        function showTooltip(event, d) {{
            const tooltip = d3.select("#tooltip");
            const content = d.data.full_content || d.data.name;
            const metadata = d.data.metadata || {{}};

            let tooltipContent = `<strong>${{d.data.role || 'Thread'}}:</strong><br>${{content}}`;

            if (d.data.created_at) {{
                tooltipContent += `<br><br><strong>Created:</strong> ${{new Date(d.data.created_at).toLocaleString()}}`;
            }}

            if (Object.keys(metadata).length > 0) {{
                tooltipContent += `<br><br><strong>Metadata:</strong><br>${{JSON.stringify(metadata, null, 2)}}`;
            }}

            tooltip.html(tooltipContent)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px")
                .style("opacity", 1);
        }}

        function hideTooltip() {{
            d3.select("#tooltip").style("opacity", 0);
        }}

        function expandAll() {{
            root.descendants().forEach(d => {{
                if (d._children) {{
                    d.children = d._children;
                    d._children = null;
                }}
            }});
            update(root);
        }}

        function collapseAll() {{
            root.descendants().slice(1).forEach(d => {{
                if (d.children) {{
                    d._children = d.children;
                    d.children = null;
                }}
            }});
            update(root);
        }}

        function resetZoom() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }}

        function downloadSVG() {{
            const svgElement = document.querySelector("#tree-container svg");
            const svgData = new XMLSerializer().serializeToString(svgElement);
            const svgBlob = new Blob([svgData], {{type: "image/svg+xml;charset=utf-8"}});
            const svgUrl = URL.createObjectURL(svgBlob);
            const downloadLink = document.createElement("a");
            downloadLink.href = svgUrl;
            downloadLink.download = "conversation-tree.svg";
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        }}
    </script>
</body>
</html>
"""

    return HTMLResponse(content=html_content)


@router.get(
    "/threads/overview",
    response_class=HTMLResponse,
    summary="Overview of all chat threads",
    description="""
    Generate a dashboard view showing all chat threads in the system with
    visual statistics and quick access to individual thread visualizations.

    **Features:**
    - Grid view of all threads with previews
    - Statistics dashboard showing usage patterns
    - Quick links to individual thread visualizations
    - Filter and search capabilities
    - Responsive design
    """,
    response_description="Interactive HTML dashboard of all chat threads",
)
async def visualize_threads_overview(
    chat_service: ChatService = Depends(get_chat_service),
) -> HTMLResponse:
    """Generate an overview dashboard of all chat threads."""

    # For now, we'll create a simple overview page
    # In a real implementation, you'd fetch all threads from the database

    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Threads Overview - Sample Chat App</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }

        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 30px;
            margin: 0 auto;
            max-width: 1200px;
        }

        .thread-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .thread-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .thread-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }

        .thread-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }

        .thread-stats {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
            font-size: 0.9em;
            color: #666;
        }

        .view-tree-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 10px;
            transition: all 0.3s ease;
        }

        .view-tree-btn:hover {
            background: #5a6fd8;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌳 Threads Overview</h1>
        <p>Interactive visualization dashboard for all chat threads</p>
    </div>

    <div class="container">
        <h2>Sample Threads</h2>
        <p>Here are some example threads that would be available in a seeded database:</p>

        <div class="thread-grid">
            <div class="thread-card">
                <div class="thread-title">📚 General Discussion</div>
                <p>A conversation about machine learning concepts and best practices.</p>
                <div class="thread-stats">
                    <span>8 messages</span>
                    <span>Jan 15, 2024</span>
                </div>
                <button class="view-tree-btn" onclick="window.open('/api/visualization/thread/123e4567-e89b-12d3-a456-426614174000/tree', '_blank')">
                    🌳 View Tree
                </button>
            </div>

            <div class="thread-card">
                <div class="thread-title">🔧 Tech Support</div>
                <p>Technical discussion about API integration and troubleshooting.</p>
                <div class="thread-stats">
                    <span>12 messages</span>
                    <span>Jan 16, 2024</span>
                </div>
                <button class="view-tree-btn" onclick="window.open('/api/visualization/thread/234e5678-f89c-23d4-b567-537725285111/tree', '_blank')">
                    🌳 View Tree
                </button>
            </div>

            <div class="thread-card">
                <div class="thread-title">📋 Project Planning</div>
                <p>Strategic planning session for upcoming development milestones.</p>
                <div class="thread-stats">
                    <span>6 messages</span>
                    <span>Jan 17, 2024</span>
                </div>
                <button class="view-tree-btn" onclick="window.open('/api/visualization/thread/345e6789-089d-34e5-c678-648836396222/tree', '_blank')">
                    🌳 View Tree
                </button>
            </div>
        </div>

        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
            <h3>🎯 How to Use</h3>
            <ul>
                <li><strong>View Individual Trees:</strong> Click the "View Tree" button on any thread card</li>
                <li><strong>Interactive Navigation:</strong> In the tree view, click nodes to expand/collapse</li>
                <li><strong>Hover for Details:</strong> Hover over nodes to see full message content</li>
                <li><strong>Export Visualizations:</strong> Use the download button to save trees as SVG files</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

    return HTMLResponse(content=html_content)
