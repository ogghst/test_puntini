from playwright.sync_api import sync_playwright, Page, expect

def login(page: Page):
    """Logs in to the application."""
    page.goto("http://localhost:5173/login")
    page.get_by_label("Username").fill("testuser")
    page.get_by_label("Password").fill("testpass")
    page.get_by_role("button", name="Login").click()
    expect(page).to_have_url("http://localhost:5173/dashboard")

def verify_graph_visualization(page: Page):
    """
    This script verifies that the graph visualization component is rendered correctly.
    """
    login(page)

    # Click on the "Graph" tab
    graph_tab = page.get_by_role("tab", name="Graph")
    expect(graph_tab).to_be_visible()
    graph_tab.click()

    # Wait for the graph to be visible
    # The graph is inside a div with a ref, so we can't directly select it.
    # Instead, we'll look for the canvas element that cytoscape creates.
    graph_canvas = page.locator("canvas[data-id='layer2-node']")
    expect(graph_canvas).to_be_visible(timeout=15000)


    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/graph_visualization.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        verify_graph_visualization(page)
    finally:
        browser.close()