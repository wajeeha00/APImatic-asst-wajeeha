import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from notion.client import NotionClient

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/tasks.readonly"]
NOTION_INTEGRATION_TOKEN = os.environ.get("NOTION_INTEGRATION_TOKEN")
NOTION_DATABASE_ID = 'https://www.notion.so/4b84888ded8f463f986bd57b3e893041?v=8730a097c3b84d6c8a983f78e92d8e5d&pvs=4'  

def main():
    google_creds = None

    if os.path.exists("token.json"):
        google_creds = Credentials.from_authorized_user_file("token.json", GOOGLE_SCOPES)

    if not google_creds or not google_creds.valid:
        if google_creds and google_creds.expired and google_creds.refresh_token:
            google_creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", GOOGLE_SCOPES)
            google_creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(google_creds.to_json())

    try:
        google_service = build("tasks", "v1", credentials=google_creds)

        # Call the Google Tasks API to get detailed task information
        results = google_service.tasks().list(tasklist="your_task_list_id").execute()
        tasks = results.get("items", [])

        if not tasks:
            print("No tasks found.")
            return

        print("Google Tasks:")
        for task in tasks:
            title = task.get("title", "")
            task_id = task.get("id", "")
            status = task.get("status", "")

            print(f"{title} ({task_id}) - Status: {status}")

            # Create a task in Notion for each Google Task
            send_task_to_notion(title, task_id, status)

    except HttpError as err:
        print(err)


def send_task_to_notion(task_title, task_id,status):
    """Send task data to Notion."""
    try:
        # Initialize Notion client
        notion_client = NotionClient(token_v2=NOTION_INTEGRATION_TOKEN)

        # Get the Notion database
        notion_db = notion_client.get_collection_view(NOTION_DATABASE_ID)

        # Create a new task in Notion
        new_task = notion_db.collection.add_row()
        new_task.title = task_title
        new_task.google_task_id = task_id
        new_task.status = status

        print(f"Task sent to Notion: {task_title} ({task_id}) - Status: {status}")

    except Exception as e:
        print(f"Error sending task to Notion: {e}")


if __name__ == "__main__":
    main()
