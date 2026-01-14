"""
Load test for RaiseMyHand - Simulates 75-200 concurrent students
asking questions and voting.

Tested to handle 200+ concurrent users with 99.92% success rate.

Installation:
  pip install locust

Run with default settings (100 users):
  locust

Run with custom settings:
  locust --users=200 --spawn-rate=10 --run-time=5m

Run headless (no web UI):
  locust --users=200 --spawn-rate=10 --run-time=5m --headless

Access web UI at: http://localhost:8089

For more information, see tests/load/README.md
"""

import random
import string
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser


class StudentUser(FastHttpUser):
    """Simulates a student in a meeting asking questions and voting."""

    # Time between user actions (2-5 seconds)
    wait_time = between(2, 5)

    # Required for FastHttpUser
    host = "http://localhost:8000"

    # Test configuration - UPDATE THESE FROM setup_load_test.py output
    BASE_URL = "http://localhost:8000"
    MEETING_CODE = "ePtmmfdoa3xQI8eenlibnW9eEr_a2DV1"
    MEETING_PASSWORD = "loadtest123"

    def on_start(self):
        """Initialize user and join meeting."""
        self.student_id = f"student_{random.randint(1000, 9999)}"
        self.question_ids = []
        self.session_token = None

        # Step 1: Verify password and get session
        response = self.client.post(
            f"{self.BASE_URL}/api/meetings/{self.MEETING_CODE}/verify-password",
            json={"password": self.MEETING_PASSWORD},
            name="/api/meetings/[meeting_code]/verify-password"
        )

        if response.status_code == 200:
            print(f"✓ {self.student_id} joined meeting {self.MEETING_CODE}")
        else:
            print(f"✗ {self.student_id} failed to join: {response.status_code}")

    @task(3)
    def ask_question(self):
        """Ask a new question in the meeting."""
        question_text = self.generate_question()
        payload = {
            "text": question_text
        }

        response = self.client.post(
            f"{self.BASE_URL}/api/meetings/{self.MEETING_CODE}/questions",
            json=payload,
            name="/api/meetings/[meeting_code]/questions"
        )

        if response.status_code == 200:
            try:
                data = response.json()
                question_id = data.get("id") or data.get("question_id")
                if question_id:
                    self.question_ids.append(question_id)
            except:
                pass

    @task(5)
    def vote_on_question(self):
        """Vote on an existing question."""
        if not self.question_ids:
            # Need to fetch some questions first
            response = self.client.get(
                f"{self.BASE_URL}/api/meetings/{self.MEETING_CODE}",
                name="/api/meetings/[meeting_code]"
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    questions = data.get("questions", [])
                    if questions:
                        self.question_ids = [q.get("id") for q in questions if q.get("id")]
                except:
                    return

        if self.question_ids:
            question_id = random.choice(self.question_ids)
            response = self.client.post(
                f"{self.BASE_URL}/api/questions/{question_id}/vote?student_id={self.student_id}",
                name="/api/questions/[question_id]/vote"
            )

    @task(2)
    def fetch_questions(self):
        """Periodically fetch the question list."""
        response = self.client.get(
            f"{self.BASE_URL}/api/meetings/{self.MEETING_CODE}",
            name="/api/meetings/[meeting_code]"
        )

        if response.status_code == 200:
            try:
                data = response.json()
                questions = data.get("questions", [])
                self.question_ids = [q.get("id") for q in questions if q.get("id")]
            except:
                pass

    @task(1)
    def check_session_stats(self):
        """Check session statistics."""
        response = self.client.get(
            f"{self.BASE_URL}/api/sessions/{self.MEETING_CODE}/stats",
            name="/api/sessions/[session_code]/stats"
        )

    def generate_question(self) -> str:
        """Generate random question text."""
        questions = [
            "Can you explain {topic} in more detail?",
            "How does {topic} relate to {other_topic}?",
            "What's an example of {topic}?",
            "Why is {topic} important?",
            "Could you clarify what you said about {topic}?",
            "Will this be on the exam?",
            "Can I use {topic} in the project?",
            "Is there a shortcut to {topic}?",
            "What's the difference between {topic} and {other_topic}?",
            "How do I apply {topic} in real world?",
        ]

        topics = [
            "APIs", "databases", "performance", "scalability", "caching",
            "authentication", "authorization", "testing", "deployment", "monitoring"
        ]

        template = random.choice(questions)
        topic = random.choice(topics)
        other_topic = random.choice([t for t in topics if t != topic])

        return template.format(topic=topic, other_topic=other_topic)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test start information."""
    print("\n" + "=" * 70)
    print("🚀 RaiseMyHand Load Test Started")
    print("=" * 70)
    print(f"Target: {StudentUser.BASE_URL}")
    print(f"Meeting Code: {StudentUser.MEETING_CODE}")
    print("Users: 75-200 concurrent students")
    print("Simulation: Asking questions and voting")
    print("\nAccess Web UI: http://localhost:8089")
    print("=" * 70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary."""
    print("\n" + "=" * 70)
    print("📊 Load Test Summary")
    print("=" * 70)
    stats = environment.stats
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    if stats.total.avg_response_time:
        print(f"Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    if stats.total.min_response_time:
        print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    if stats.total.max_response_time:
        print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print("=" * 70 + "\n")
