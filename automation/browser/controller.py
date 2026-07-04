import os
import time
import base64
from playwright.sync_api import sync_playwright
from typing import Tuple, Dict, Any, List

class BrowserController:
    """
    Playwright-based controller that attaches to a running Chrome instance
    via the remote debugging port, extracts game states, and interacts with the GUI.
    """
    def __init__(self, debug_ws_url: str = "http://localhost:9222"):
        self.debug_ws_url = debug_ws_url
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.grid_selector = ".penalty-grid-container, #penalty-game-canvas, .game-board" # fallback selectors
        self.target_selector_template = ".penalty-target[data-id='{}'], .spot-{}" # template selectors
        self.connect()

    def connect(self):
        try:
            self.playwright = sync_playwright().start()
            # Connect to existing Chrome session using remote debugging
            self.browser = self.playwright.chromium.connect_over_cdp(self.debug_ws_url)
            self.context = self.browser.contexts[0]
            
            # Find the active page/tab playing the penalty game
            pages = self.context.pages
            if not pages:
                # If no pages exist, create one
                self.page = self.context.new_page()
            else:
                # Look for a page containing 'penalty' or default to the active tab
                for p in pages:
                    if "penalty" in p.url.lower() or "game" in p.url.lower():
                        self.page = p
                        break
                if not self.page:
                    self.page = pages[0]
            
            # Set default timeout
            self.page.set_default_timeout(10000)
            print(f"Successfully attached to page: {self.page.url}")
        except Exception as e:
            print(f"Error connecting to Chrome debugging instance: {e}")
            print("Running in simulated browser mode. Please ensure Chrome is running with remote-debugging-port=9222")
            self.page = None

    def get_state(self) -> Dict[str, Any]:
        """
        Reads active game grid multipliers and state from the DOM.
        """
        grid = [0] * 12
        multiplier = 1.0
        
        if not self.page:
            return {"grid": grid, "multiplier": multiplier}
            
        try:
            # Locate all selected targets to populate the active state grid
            # In a real penalty game, we check the DOM for elements marked as 'hit', 'score', or 'miss'
            hit_spots = self.page.locator(".penalty-target.hit, .spot.scored, .spot.missed").all()
            for spot in hit_spots:
                spot_id = spot.get_attribute("data-id") or spot.get_attribute("id")
                if spot_id and spot_id.isdigit():
                    idx = int(spot_id)
                    if 0 <= idx < 12:
                        grid[idx] = 1
            
            # Extract multiplier text from DOM
            mult_el = self.page.locator(".current-multiplier, .payout-mult, .game-info .value").first
            if mult_el.is_visible():
                mult_txt = mult_el.text_content() or "1.0"
                # Strip symbols like 'x' or whitespace
                mult_txt = mult_txt.replace("x", "").replace("X", "").strip()
                try:
                    multiplier = float(mult_txt)
                except ValueError:
                    pass
        except Exception as e:
            print(f"Error extracting game state: {e}")
            
        return {"grid": grid, "multiplier": multiplier}

    def click_target(self, action: int) -> Tuple[bool, float, str]:
        """
        Executes click action on specified target (0-11) in 3x4 grid.
        Returns:
            success (bool): Did the shot score?
            payout (float): The current round payout.
            outcome (str): 'WIN', 'LOSS', or 'ERROR'.
        """
        if not self.page:
            # Browser mock fallback
            return (True, 1.15, "WIN")
            
        try:
            # 1. Attempt clicking by matching dynamic selectors
            clicked = False
            for selector_pattern in [".penalty-target[data-id='{}']", ".spot-{}", "#spot-{}"]:
                selector = selector_pattern.format(action)
                target = self.page.locator(selector)
                if target.is_visible() and target.is_enabled():
                    target.click()
                    clicked = True
                    break
            
            # 2. Fallback: coordinate-based grid click if grid selector is found
            if not clicked:
                grid_container = self.page.locator(self.grid_selector).first
                if grid_container.is_visible():
                    box = grid_container.bounding_box()
                    if box:
                        # Compute 3x4 grid center offsets
                        col = action % 4
                        row = action // 4
                        
                        cell_w = box["width"] / 4
                        cell_h = box["height"] / 3
                        
                        click_x = box["x"] + (col * cell_w) + (cell_w / 2)
                        click_y = box["y"] + (row * cell_h) + (cell_h / 2)
                        
                        self.page.mouse.click(click_x, click_y)
                        clicked = True
            
            if not clicked:
                # Last resort: click general body coordinates or return error
                print(f"Could not locate element for target {action}, simulating generic click")
                return (False, 0.0, "ERROR")
                
            # Wait for animation to resolve (typically ~1.5 - 2.0s)
            time.sleep(1.8)
            
            # Determine outcome (Scored/Saved)
            # We look for text overlays indicating "Goal" or visual cues
            status_text = self.page.locator(".game-status-text, .result-overlay").first
            if status_text.is_visible():
                txt = (status_text.text_content() or "").lower()
                if "goal" in txt or "win" in txt or "score" in txt:
                    return (True, self.get_state()["multiplier"], "WIN")
                elif "save" in txt or "miss" in txt or "lose" in txt:
                    return (False, 0.0, "LOSS")
            
            # Fallback check based on cashout/collect button state
            cashout_btn = self.page.locator(".cashout-button, .collect-btn").first
            if cashout_btn.is_visible() and cashout_btn.is_enabled():
                return (True, self.get_state()["multiplier"], "WIN")
            else:
                return (False, 0.0, "LOSS")
                
        except Exception as e:
            print(f"Action execution error on target {action}: {e}")
            return (False, 0.0, "ERROR")

    def reset_game(self) -> bool:
        """
        Clicks "New Round" or "Cashout" button to reset Penalty board state.
        """
        if not self.page:
            return True
            
        try:
            # Try cashout/collect button first
            collect_btn = self.page.locator(".cashout-button, .collect-btn, button:has-text('Collect'), button:has-text('Cash Out')").first
            if collect_btn.is_visible() and collect_btn.is_enabled():
                collect_btn.click()
                time.sleep(1.0)
                return True
                
            # Try new game/reset button
            reset_btn = self.page.locator(".new-game-btn, button:has-text('New Game'), button:has-text('Play')").first
            if reset_btn.is_visible() and reset_btn.is_enabled():
                reset_btn.click()
                time.sleep(1.0)
                return True
        except Exception as e:
            print(f"Error resetting game board: {e}")
            
        return False

    def capture_screenshot(self) -> str:
        """
        Captures a screenshot of the active browser screen and encodes it as Base64.
        """
        if not self.page:
            # Return dummy base64 pixel image
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
            
        try:
            # Capture viewport screenshot (or locate game-board specifically to crop)
            screenshot_bytes = self.page.screenshot(type="jpeg", quality=60)
            encoded = base64.b64encode(screenshot_bytes).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded}"
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return ""

    def disconnect(self):
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
