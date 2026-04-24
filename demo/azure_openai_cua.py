import argparse
import os
import asyncio
import base64
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from playwright.async_api import async_playwright, TimeoutError

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://ai.azure.com/.default"
)

# Configuration
BASE_URL = "https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/"
MODEL = "gpt-5.4"
DISPLAY_WIDTH = 1440
DISPLAY_HEIGHT = 900
ITERATIONS = 5  # Max number of iterations before forcing the model to return control to the human supervisor

# Key mapping for special keys in Playwright
# Supports multiple common spellings for each key (case-insensitive)
KEY_MAPPING = {
    "/": "Slash", "\\": "Backslash",
    "alt": "Alt", "option": "Alt",
    "arrowdown": "ArrowDown", "down": "ArrowDown",
    "arrowleft": "ArrowLeft", "left": "ArrowLeft",
    "arrowright": "ArrowRight", "right": "ArrowRight",
    "arrowup": "ArrowUp", "up": "ArrowUp",
    "backspace": "Backspace",
    "ctrl": "Control", "control": "Control",
    "cmd": "Meta", "command": "Meta", "meta": "Meta", "win": "Meta", "super": "Meta",
    "delete": "Delete",
    "enter": "Enter", "return": "Return",
    "esc": "Escape", "escape": "Escape",
    "shift": "Shift",
    "space": " ",
    "tab": "Tab",
    "pagedown": "PageDown", "pageup": "PageUp",
    "home": "Home", "end": "End",
    "insert": "Insert",
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
    "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
    "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12"
}

last_successful_screenshot = None


def validate_coordinates(x, y):
    """Ensure coordinates are within display bounds."""
    return max(0, min(x, DISPLAY_WIDTH)), max(0, min(y, DISPLAY_HEIGHT))


async def handle_action(page, action):
    """Handle different action types from the model."""
    action_type = action.get("type")

    if action_type == "click":
        button = action.get("button", "left")
        x, y = validate_coordinates(action.get("x"), action.get("y"))

        print(f"\tAction: click at ({x}, {y}) with button '{button}'")

        if button == "back":
            await page.go_back()
        elif button == "forward":
            await page.go_forward()
        elif button == "wheel":
            await page.mouse.wheel(x, y)
        else:
            button_type = {"left": "left", "right": "right", "middle": "middle"}.get(button, "left")
            await page.mouse.click(x, y, button=button_type)
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=3000)
            except TimeoutError:
                pass

    elif action_type == "double_click":
        x, y = validate_coordinates(action.get("x"), action.get("y"))
        print(f"\tAction: double click at ({x}, {y})")
        await page.mouse.dblclick(x, y)

    elif action_type == "drag":
        path = action.get("path", [])
        if len(path) < 2:
            print("\tAction: drag requires at least 2 points. Skipping.")
            return
        start = path[0]
        sx, sy = validate_coordinates(start.get("x", 0), start.get("y", 0))
        print(f"\tAction: drag from ({sx}, {sy}) through {len(path) - 1} points")
        await page.mouse.move(sx, sy)
        await page.mouse.down()
        for point in path[1:]:
            px, py = validate_coordinates(point.get("x", 0), point.get("y", 0))
            await page.mouse.move(px, py)
        await page.mouse.up()

    elif action_type == "move":
        x, y = validate_coordinates(action.get("x"), action.get("y"))
        print(f"\tAction: move to ({x}, {y})")
        await page.mouse.move(x, y)

    elif action_type == "scroll":
        scroll_x = action.get("scroll_x", 0)
        scroll_y = action.get("scroll_y", 0)
        x, y = validate_coordinates(action.get("x"), action.get("y"))

        print(f"\tAction: scroll at ({x}, {y}) with offsets ({scroll_x}, {scroll_y})")
        await page.mouse.move(x, y)
        await page.evaluate(f"window.scrollBy({{left: {scroll_x}, top: {scroll_y}, behavior: 'smooth'}});")

    elif action_type == "keypress":
        keys = action.get("keys", [])
        print(f"\tAction: keypress {keys}")
        mapped_keys = [KEY_MAPPING.get(key.lower(), key) for key in keys]

        if len(mapped_keys) > 1:
            # For key combinations (like Ctrl+C)
            for key in mapped_keys:
                await page.keyboard.down(key)
            await asyncio.sleep(0.1)
            for key in reversed(mapped_keys):
                await page.keyboard.up(key)
        else:
            for key in mapped_keys:
                await page.keyboard.press(key)

    elif action_type == "type":
        text = action.get("text", "")
        print(f"\tAction: type text: {text}")
        await page.keyboard.type(text, delay=20)

    elif action_type == "wait":
        ms = action.get("ms", 1000)
        print(f"\tAction: wait {ms}ms")
        await asyncio.sleep(ms / 1000)

    elif action_type == "screenshot":
        print("\tAction: screenshot")

    else:
        print(f"\tUnrecognized action: {action_type}")


async def take_screenshot(page):
    """Take a screenshot and return base64 encoding with caching for failures."""
    global last_successful_screenshot

    try:
        screenshot_bytes = await page.screenshot(full_page=False)
        last_successful_screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
        return last_successful_screenshot
    except Exception as e:
        print(f"Screenshot failed: {e}")
        if last_successful_screenshot:
            return last_successful_screenshot


async def process_model_response(client, response, page, max_iterations=ITERATIONS):
    """Process the model's response and execute actions."""
    for iteration in range(max_iterations):
        if not response.output:
            print("No output from model.")
            break

        response_id = response.id
        print(f"\nIteration {iteration + 1} - Response ID: {response_id}\n")

        # Print text responses and reasoning
        for item in response.output:
            if item.type == "text":
                print(f"\nModel message: {item.text}\n")

            if item.type == "reasoning" and item.summary:
                print("=== Model Reasoning ===")
                for summary in item.summary:
                    if hasattr(summary, 'text') and summary.text.strip():
                        print(summary.text)
                print("=====================\n")

        # Extract computer calls
        computer_calls = [item for item in response.output if item.type == "computer_call"]

        if not computer_calls:
            print("No computer call found in response. Reverting control to human supervisor")
            break

        computer_call = computer_calls[0]
        call_id = computer_call.call_id
        actions = computer_call.actions  # actions is a batched array of dicts

        # Handle safety checks
        acknowledged_checks = []
        if computer_call.pending_safety_checks:
            pending_checks = computer_call.pending_safety_checks
            print("\nSafety checks required:")
            for check in pending_checks:
                print(f"- {check.code}: {check.message}")

            if input("\nDo you want to proceed? (y/n): ").lower() != 'y':
                print("Operation cancelled by user.")
                break

            acknowledged_checks = pending_checks

        # Execute all actions in the batch, in order
        try:
            await page.bring_to_front()
            for action in actions:
                await handle_action(page, action)

                # Check if a new page was created after a click action
                if action.get("type") == "click":
                    await asyncio.sleep(1.5)
                    all_pages = page.context.pages
                    if len(all_pages) > 1:
                        newest_page = all_pages[-1]
                        if newest_page != page and newest_page.url not in ["about:blank", ""]:
                            print(f"\tSwitching to new tab: {newest_page.url}")
                            page = newest_page
                elif action.get("type") != "wait":
                    await asyncio.sleep(0.5)

        except Exception as e:
            print(f"Error handling action: {e}")
            import traceback
            traceback.print_exc()

        # Take a screenshot after the actions
        screenshot_base64 = await take_screenshot(page)
        print("\tNew screenshot taken")

        # Prepare input for the next request
        input_content = [{
            "type": "computer_call_output",
            "call_id": call_id,
            "output": {
                "type": "computer_screenshot",
                "image_url": f"data:image/png;base64,{screenshot_base64}",
                "detail": "original"
            }
        }]

        # Add acknowledged safety checks if any
        if acknowledged_checks:
            input_content[0]["acknowledged_safety_checks"] = [
                {"id": check.id, "code": check.code, "message": check.message}
                for check in acknowledged_checks
            ]

        # Send the screenshot back for the next step
        try:
            response = client.responses.create(
                model=MODEL,
                previous_response_id=response_id,
                tools=[{"type": "computer"}],
                input=input_content,
            )
            print("\tModel processing screenshot")
        except Exception as e:
            print(f"Error in API call: {e}")
            import traceback
            traceback.print_exc()
            break

    if iteration >= max_iterations - 1:
        print("Reached maximum number of iterations. Stopping.")


async def run_task(client, page, user_input):
    """Run a single task against the model."""
    screenshot_base64 = await take_screenshot(page)
    print("\nTake initial screenshot")

    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "computer"}],
        instructions=(
            "You are an AI agent with the ability to control a browser. You can control the keyboard "
            "and mouse. You take a screenshot after each action to check if your action was successful. "
            "Once you have completed the requested task you should stop running and pass back control "
            "to your human supervisor."
        ),
        input=[{
            "role": "user",
            "content": [{
                "type": "input_text",
                "text": user_input
            }, {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{screenshot_base64}",
                "detail": "original"
            }]
        }],
        reasoning={"summary": "concise"},
    )
    print("\nSending model initial screenshot and instructions")

    await process_model_response(client, response, page)


async def main():
    parser = argparse.ArgumentParser(description="Run Azure OpenAI CUA agent with a custom task.")
    parser.add_argument(
        "--task",
        type=str,
        default="",
        help="Task prompt for the agent. If omitted, the agent runs in interactive mode.",
    )
    args = parser.parse_args()

    # Initialize OpenAI client
    client = OpenAI(
        base_url=BASE_URL,
        api_key=token_provider
    )

    # Initialize Playwright
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            args=[f"--window-size={DISPLAY_WIDTH},{DISPLAY_HEIGHT}", "--disable-extensions"]
        )

        context = await browser.new_context(
            viewport={"width": DISPLAY_WIDTH, "height": DISPLAY_HEIGHT},
            accept_downloads=True
        )

        page = await context.new_page()

        # Navigate to starting page
        await page.goto("https://www.bing.com", wait_until="domcontentloaded")
        print("Browser initialized to Bing.com")

        try:
            if args.task:
                # Non-interactive mode: run a single task supplied via --task
                await run_task(client, page, args.task)
            else:
                # Interactive mode: prompt the user in a loop
                while True:
                    print("\n" + "=" * 50)
                    user_input = input("Enter a task to perform (or 'exit' to quit): ")

                    if user_input.lower() in ('exit', 'quit'):
                        break

                    if not user_input.strip():
                        continue

                    await run_task(client, page, user_input)

        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await context.close()
            await browser.close()
            print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
