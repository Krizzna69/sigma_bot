import time
import json
import http.client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Connection details for RapidAPI's Instagram Scraper API
API_HOST = "instagram-scraper-api2.p.rapidapi.com"
API_KEY = '77c3fc0858msheb391c7d2421e57p1dc3e1jsn49c69c412cd2'  # Replace with your valid API key

headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': API_HOST
}


# Categorizing comments into high, medium, and low risk based on keywords or length (Example criteria)
def categorize_comment(comment):
    high_risk_keywords = ['spam', 'scam', 'fake']
    medium_risk_keywords = ['free', 'offer', 'deal']

    # Define categories based on the content of the comment
    if any(keyword in comment.lower() for keyword in high_risk_keywords):
        return 'high'
    elif any(keyword in comment.lower() for keyword in medium_risk_keywords):
        return 'medium'
    else:
        return 'low'


# Categorize each comment
categorized_comments = {'high': [], 'medium': [], 'low': []}


def categorize_all_comments(all_comments):
    for comment in all_comments:
        risk_category = categorize_comment(comment)
        categorized_comments[risk_category].append(comment)

    # Sort the comments into their respective categories
    sorted_high_risk = sorted(categorized_comments['high'], key=lambda x: len(x), reverse=True)
    sorted_medium_risk = sorted(categorized_comments['medium'], key=lambda x: len(x), reverse=True)
    sorted_low_risk = sorted(categorized_comments['low'], key=lambda x: len(x), reverse=True)

    return sorted_high_risk, sorted_medium_risk, sorted_low_risk


# Create HTML for each category
def create_category_html(comments, category):
    return "".join(
        f"<div style='margin-bottom:10px; padding:5px; border:1px solid {category_color[category]}; background-color:{category_bg_color[category]};'>{comment}</div>"
        for comment in comments
    )


# Define category-specific colors
category_color = {'high': 'red', 'medium': 'orange', 'low': 'green'}
category_bg_color = {'high': '#ffe6e6', 'medium': '#fff3e6', 'low': '#e6f7e6'}


# Dashboard HTML

def generate_dashboard_html(spam_comments):
    import json  # For safely encoding HTML in JS

    # Function to generate HTML for spam comments
    def create_spam_comments_html(comments):
        return "".join(f"""
            <div style="margin-bottom: 12px; padding: 12px; border: 1px solid #b0bec5; background-color: rgba(255, 235, 59, 0.1);
                border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease-in-out;">
                <p style="font-size: 16px; line-height: 1.5; font-weight: 500; color: #444;">
                    {comment}</p>
            </div>
        """ for comment in comments)

    # Generate the HTML for spam comments and escape for JS
    spam_html = json.dumps(create_spam_comments_html(spam_comments))  # Escaped HTML
    dashboard_html = json.dumps(f"""
        <div id="spam-dashboard" style="display: none; position: fixed; top: 0; left: 0; width: 100%; background-color: #00796b; color: white;
                    padding: 10px 30px; font-size: 18px; text-align: center; z-index: 1100;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); border-bottom: 5px solid #004d40; font-family: 'Arial', sans-serif;">
            <strong style="font-weight: 700;">Spam Comments Dashboard</strong>
            <div style="margin-top: 10px; font-size: 16px;">
                <strong>Total Spam Comments:</strong> <span id="spam-count" style="color: #FFEB3B; font-size: 22px; font-weight: 600;">{len(spam_comments)}</span>
            </div>
            <div style="margin-top: 10px; color: #FFEB3B;">
                <button id="toggle-spam-popup" style="font-size: 16px; background-color: #FFEB3B; border: none; padding: 8px 12px;
                    color: #00796b; cursor: pointer; border-radius: 5px; font-weight: bold;">
                    Show Spam Comments
                </button>
            </div>
        </div>
    """)

    # JavaScript code for interactivity
    script = f"""
        (function() {{
            let spamComments = {spam_html}; // Initial spam comments
            const dashboardHtml = {dashboard_html}; // Dashboard HTML

            // Add spam logo to toggle dashboard
            if (!document.getElementById('spam-logo')) {{
                const spamLogo = document.createElement('div');
                spamLogo.id = 'spam-logo';
                spamLogo.innerText = '🚫';
                spamLogo.style.cssText = `
                    position: fixed; bottom: 30px; right: 30px; font-size: 40px;
                    cursor: pointer; padding: 10px; z-index: 1101;
                `;
                document.body.appendChild(spamLogo);

                spamLogo.onclick = () => {{
                    const dashboard = document.getElementById('spam-dashboard');
                    if (dashboard) dashboard.style.display = 'block';
                    const popup = document.getElementById('spam-popup');
                    if (popup) popup.style.display = 'block';
                }};
            }}

            // Create spam dashboard
            if (!document.getElementById('spam-dashboard')) {{
                const dashboard = document.createElement('div');
                dashboard.id = 'spam-dashboard';
                dashboard.innerHTML = dashboardHtml;
                document.body.appendChild(dashboard);

                document.getElementById('toggle-spam-popup').onclick = () => {{
                    const popup = document.getElementById('spam-popup');
                    popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
                }};
            }}

            // Create spam popup
            if (!document.getElementById('spam-popup')) {{
                const popup = document.createElement('div');
                popup.id = 'spam-popup';
                popup.style.cssText = `
                    position: fixed; bottom: 80px; right: 30px; max-width: 400px; max-height: 480px;
                    overflow-y: auto; padding: 20px 30px; background-color: #ffffff;
                    border-radius: 12px; color: #333; box-shadow: 0px 6px 20px rgba(0, 0, 0, 0.2);
                    z-index: 1100; display: none;
                `;
                popup.innerHTML = `
                    <button id="close-popup" style="position: absolute; top: 10px; right: 10px; background-color: #f44336; color: white;
                        border: none; padding: 5px 10px; border-radius: 5px; font-size: 14px; cursor: pointer;">Close</button>
                    ` + spamComments;
                document.body.appendChild(popup);

                document.getElementById('close-popup').onclick = () => {{
                    popup.style.display = 'none';
                }};
            }}

            // Function to update popup content with latest comments
            function updatePopupContent() {{
                const popup = document.getElementById('spam-popup');
                if (popup) {{
                    popup.innerHTML = `
                        <button id="close-popup" style="position: absolute; top: 10px; right: 10px; background-color: #f44336; color: white;
                            border: none; padding: 5px 10px; border-radius: 5px; font-size: 14px; cursor: pointer;">Close</button>
                        ` + spamComments;

                    document.getElementById('close-popup').onclick = () => {{
                        popup.style.display = 'none';
                    }};

                    const count = spamComments.split('</div>').length - 1; // Count comments
                    document.getElementById('spam-count').textContent = count;
                }}
            }}

            // Simulate adding a new spam comment (for testing purposes)
            setTimeout(() => {{
                spamComments += `
                    <div style="margin-bottom: 12px; padding: 12px; border: 1px solid #b0bec5; background-color: rgba(255, 235, 59, 0.1);
                        border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                        <p style="font-size: 16px; line-height: 1.5; font-weight: 500; color: #444;">This is a new spam comment</p>
                    </div>
                `;
                updatePopupContent();
            }}, 5000); // Adds a new comment after 5 seconds
        }})();
    """
    return script


def inject_spam_comments(driver, spam_comments):
    """
    Dynamically inject a popup displaying spam comments in the browser.

    Args:
        driver: Selenium WebDriver instance.
        spam_comments: List of spam comments.
    """
    if not spam_comments:
        return  # No spam comments, do nothing

    spam_html = "".join(
        f"<div style='margin-bottom:10px; padding:5px; border:1px solid red; background-color:#ffe6e6;'>{comment}</div>"
        for comment in spam_comments
    )

    script = f"""
        var popup = document.createElement('div');
        popup.id = 'spam-popup';
        popup.style.position = 'fixed';
        popup.style.bottom = '20px';
        popup.style.right = '20px';
        popup.style.width = '300px';
        popup.style.maxHeight = '400px';
        popup.style.overflowY = 'auto';
        popup.style.padding = '10px';
        popup.style.border = '1px solid #ccc';
        popup.style.borderRadius = '8px';
        popup.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
        popup.style.backgroundColor = 'white';
        popup.style.color = 'black';
        popup.style.zIndex = '1000';

        var closeButton = document.createElement('button');
        closeButton.innerText = 'Close';
        closeButton.style.position = 'absolute';
        closeButton.style.top = '5px';
        closeButton.style.right = '10px';
        closeButton.style.cursor = 'pointer';
        closeButton.onclick = function() {{
            popup.remove();
        }};
        popup.appendChild(closeButton);

        var spamContent = document.createElement('div');
        spamContent.innerHTML = `{spam_html}`;
        popup.appendChild(spamContent);

        document.body.appendChild(popup);
    """
    driver.execute_script(script)


def fetch_instagram_comments(post_url):
    """
    Fetch comments from an Instagram post using RapidAPI's Instagram Scraper API.

    Args:
        post_url (str): URL of the Instagram post.

    Returns:
        tuple: Two lists - one for all comments and another for detected spam comments.
    """
    post_id = post_url.split("/")[-2]
    endpoint = f"/v1/comments?code_or_id_or_url={post_id}"

    try:
        conn = http.client.HTTPSConnection(API_HOST)
        conn.request("GET", endpoint, headers=headers)
        response = conn.getresponse()
        status = response.status
        raw_data = response.read()
        decoded_data = raw_data.decode("utf-8", errors="replace")

        if status == 200:
            json_data = json.loads(decoded_data)
            items = json_data.get("data", {}).get("items", [])

            all_comments = []
            spam_comments = []

            for item in items:
                comment_text = item.get("text", "No text available")
                if comment_text != "No text available":
                    all_comments.append(comment_text)
                    if detect_spam(comment_text):
                        spam_comments.append(comment_text)

            return all_comments, spam_comments
        else:
            print(f"Error fetching comments: Status Code {status}")
            return [], []  # Return empty lists for any error code
    finally:
        conn.close()


def detect_spam(comment_text):
    spam_keywords = []
    with open("output_list.txt", "r", encoding="utf-8") as file:
        # Read all lines from the file and add them to the list
        spam_keywords = [line.strip() for line in file.readlines()]
    comment_lower = comment_text.lower()
    return any(keyword in comment_lower for keyword in spam_keywords)




def fetch_instagram_comments(post_url):
    """
    Fetch all comments from an Instagram post using RapidAPI's Instagram Scraper API, with pagination.

    Args:
        post_url (str): URL of the Instagram post.

    Returns:
        tuple: Two lists - one for all comments and another for detected spam comments.
    """
    post_id = post_url.split("/")[-2]  # Extracting the post ID from the URL
    endpoint = f"/v1/comments?code_or_id_or_url={post_id}"

    all_comments = []
    spam_comments = []
    next_cursor = None  # This will help us paginate

    while True:
        # If we have a next_cursor, we paginate to the next set of comments
        if next_cursor:
            endpoint = f"/v1/comments?code_or_id_or_url={post_id}&cursor={next_cursor}"

        try:
            conn = http.client.HTTPSConnection(API_HOST)
            conn.request("GET", endpoint, headers=headers)
            response = conn.getresponse()
            status = response.status
            raw_data = response.read()
            decoded_data = raw_data.decode("utf-8", errors="replace")

            if status == 200:
                json_data = json.loads(decoded_data)
                items = json_data.get("data", {}).get("items", [])
                next_cursor = json_data.get("data", {}).get("next_cursor", None)  # Check for next page of comments

                # Collect comments
                for item in items:
                    comment_text = item.get("text", "No text available")
                    if comment_text != "No text available":
                        all_comments.append(comment_text)
                        if detect_spam(comment_text):  # Check if the comment is spam
                            spam_comments.append(comment_text)

                # Logging the number of comments fetched so far
                print(f"Fetched {len(all_comments)} comments so far...")

                # If no next_cursor, it means we've fetched all comments
                if not next_cursor:
                    break

            else:
                print(f"Error fetching comments: Status Code {status}")
                break  # Exit loop on error
        finally:
            conn.close()

    return all_comments, spam_comments


def open_browser_and_get_url():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("C:/Program Files/Google/Chrome/Application/chrome.exe")
    driver = webdriver.Chrome()

    try:
        driver.get("https://www.instagram.com/")
        time.sleep(10)

        while True:
            reel_url = driver.current_url  # Get the URL of the Instagram post the user is viewing
            print(f"Fetching comments for URL: {reel_url}")

            all_comments, spam_comments = fetch_instagram_comments(reel_url)

            # Categorize and sort comments
            sorted_high_risk, sorted_medium_risk, sorted_low_risk = categorize_all_comments(all_comments)

            # Inject the spam comments dashboard
            script = generate_dashboard_html(spam_comments)
            driver.execute_script(script)

            time.sleep(10)  # Wait before checking another post
    finally:
        driver.quit()


def main():
    open_browser_and_get_url()


if __name__ == "__main__":
    main()
