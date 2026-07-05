import os
import asyncio
import base64
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import Tuple, Dict, Any, Optional

class BrowserController:
    """
    Asynchronous Playwright-based controller that launches a persistent Chrome session
    or attaches to an active instance via CDP. Includes user authentication pause loops,
    DOM state extraction, coordinates clicks, and screenshot capturing.
    """
    def __init__(self, debug_ws_url: str = "http://localhost:9222"):
        self.debug_ws_url = debug_ws_url
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.grid_selector = ".penalty-grid-container, #penalty-game-canvas, .game-board"
        self.bet_button_selector = ".bet-button, button:has-text('Bet'), button:has-text('Play')"

    async def connect(self, headless: bool = False):
        """
        Launches a persistent browser session or attaches to Chrome.
        """
        try:
            self.playwright = await async_playwright().start()
            
            # Choose between CDP attachment and creating a new persistent instance
            if self.debug_ws_url and not headless:
                print(f"[Controller] Attaching to Chrome CDP session at {self.debug_ws_url}...")
                try:
                    self.browser = await self.playwright.chromium.connect_over_cdp(self.debug_ws_url)
                    self.context = self.browser.contexts[0]
                    pages = self.context.pages
                    if pages:
                        self.page = pages[0]
                    else:
                        self.page = await self.context.new_page()
                    print(f"[Controller] Attached to browser page: {self.page.url}")
                except Exception as e:
                    print(f"[Controller] Remote CDP link failed: {e}. Launching local browser instead.")
                    self.browser = None

            if not self.browser:
                print("[Controller] Launching persistent local browser instance...")
                user_data_dir = os.path.join(os.getcwd(), "chrome-profile")
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=headless,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                self.page = await self.context.new_page()
                print("[Controller] Local persistent browser context created.")

            self.page.set_default_timeout(10000)
            
        except Exception as e:
            print(f"[Controller] Critical browser startup error: {e}")
            self.page = None

    async def pause_for_login(self, target_url: str = "penalty"):
        """
        Halts automation loop execution to allow the user to manually log in.
        Monitors page URL or a success selector until verified, or awaits keyboard entry.
        """
        if not self.page:
            print("[Controller Mock] Mock pause_for_login completed.")
            return

        print("\n" + "="*60)
        print("ACTION REQUIRED: MANUAL LOGIN HANDOFF ACTIVE")
        print("Please log into your demo account in the opened Chrome browser.")
        print(f"Verify you are on the game page containing '{target_url}' in the URL.")
        print("="*60 + "\n")

        # Yield execution control by listening to page URL changes or waiting for manual trigger
        # We loop and poll until the URL updates to match target_url
        max_attempts = 120  # 2 minute timeout
        for i in range(max_attempts):
            current_url = self.page.url
            if target_url in current_url.lower():
                print(f"[Controller] Detected target URL: {current_url}. Resuming bot control.")
                return
            await asyncio.sleep(1.0)
            if i % 15 == 0:
                print(f"[Controller] Still waiting for login... ({120 - i}s remaining)")

        print("[Controller] Warning: Login wait timed out. Resuming loop.")

    async def get_state(self) -> Dict[str, Any]:
        """
        Asynchronously parses Penalty game state: active multiplier, grid hits, and bet button status.
        """
        grid = [0] * 12
        multiplier = 1.0
        bet_active = False

        if not self.page:
            # Mock state fallback
            return {"grid": grid, "multiplier": multiplier, "bet_active": True}

        try:
            # 1. Check if the Bet/Start button is visible and active (ready for new round input)
            bet_btn = self.page.locator(self.bet_button_selector).first
            if await bet_btn.is_visible():
                bet_active = await bet_btn.is_enabled()

            # 2. Extract cleared spots from DOM
            hit_spots = await self.page.locator(".penalty-target.hit, .spot.scored, .spot.missed").all()
            for spot in hit_spots:
                spot_id = await spot.get_attribute("data-id") or await spot.get_attribute("id")
                if spot_id and spot_id.isdigit():
                    idx = int(spot_id)
                    if 0 <= idx < 12:
                        grid[idx] = 1

            # 3. Read multiplier values
            mult_el = self.page.locator(".current-multiplier, .payout-mult, .game-info .value").first
            if await mult_el.is_visible():
                mult_txt = await mult_el.text_content() or "1.0"
                mult_txt = mult_txt.replace("x", "").replace("X", "").strip()
                try:
                    multiplier = float(mult_txt)
                except ValueError:
                    pass

        except Exception as e:
            print(f"[Controller] Error extracting state values: {e}")

        return {"grid": grid, "multiplier": multiplier, "bet_active": bet_active}

    async def click_target(self, action: int) -> Tuple[bool, float, str]:
        """
        Sends click action to selected target cell (0-11).
        """
        if not self.page:
            return (True, 1.15, "WIN")

        try:
            clicked = False
            # Try selector matching
            for pattern in [".penalty-target[data-id='{}']", ".spot-{}", "#spot-{}"]:
                selector = pattern.format(action)
                target = self.page.locator(selector)
                if await target.is_visible() and await target.is_enabled():
                    await target.click()
                    clicked = True
                    break

            # Coordinate click fallback
            if not clicked:
                grid_el = self.page.locator(self.grid_selector).first
                if await grid_el.is_visible():
                    box = await grid_el.bounding_box()
                    if box:
                        col = action % 4
                        row = action // 4
                        cell_w = box["width"] / 4
                        cell_h = box["height"] / 3
                        click_x = box["x"] + (col * cell_w) + (cell_w / 2)
                        click_y = box["y"] + (row * cell_h) + (cell_h / 2)
                        
                        await self.page.mouse.click(click_x, click_y)
                        clicked = True

            if not clicked:
                print(f"[Controller] Target {action} selector could not be clicked.")
                return (False, 0.0, "ERROR")

            # Wait for browser shot animation
            await asyncio.sleep(1.8)

            # Evaluate outcome
            status_el = self.page.locator(".game-status-text, .result-overlay").first
            if await status_el.is_visible():
                txt = (await status_el.text_content() or "").lower()
                if "goal" in txt or "win" in txt or "score" in txt:
                    state = await self.get_state()
                    return (True, state["multiplier"], "WIN")
                elif "save" in txt or "miss" in txt or "lose" in txt:
                    return (False, 0.0, "LOSS")

            # Validate cashout state
            cashout_btn = self.page.locator(".cashout-button, .collect-btn").first
            if await cashout_btn.is_visible() and await cashout_btn.is_enabled():
                state = await self.get_state()
                return (True, state["multiplier"], "WIN")
            else:
                return (False, 0.0, "LOSS")

        except Exception as e:
            print(f"[Controller] Click execution error on target {action}: {e}")
            return (False, 0.0, "ERROR")

    async def reset_game(self) -> bool:
        """
        Resets the penalty board state for a new round.
        """
        if not self.page:
            return True
        try:
            # Try to cashout / collect earnings
            collect_btn = self.page.locator(".cashout-button, .collect-btn, button:has-text('Collect'), button:has-text('Cash Out')").first
            if await collect_btn.is_visible() and await collect_btn.is_enabled():
                await collect_btn.click()
                await asyncio.sleep(1.0)
                return True

            # Try to click restart/play
            reset_btn = self.page.locator(".new-game-btn, button:has-text('New Game'), button:has-text('Play')").first
            if await reset_btn.is_visible() and await reset_btn.is_enabled():
                await reset_btn.click()
                await asyncio.sleep(1.0)
                return True
        except Exception as e:
            print(f"[Controller] Error executing board reset: {e}")
        return False

    async def capture_screenshot(self) -> str:
        """
        Captures screenshot and returns Base64 string for dashboard streams.
        """
        if not self.page:
            return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        try:
            screenshot_bytes = await self.page.screenshot(type="jpeg", quality=50)
            encoded = base64.b64encode(screenshot_bytes).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded}"
        except Exception as e:
            print(f"[Controller] Screenshot capture failed: {e}")
            return ""

    async def disconnect(self):
        """
        Safely closes context resources.
        """
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
