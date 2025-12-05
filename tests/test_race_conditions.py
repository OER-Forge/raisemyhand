#!/usr/bin/env python3
"""
Test script to verify race condition fixes for question numbering and vote counting.
"""
import asyncio
import aiohttp
import time

BASE_URL = "http://localhost:8000"

async def create_session_and_test():
    """Create a test session and test concurrent operations."""
    async with aiohttp.ClientSession() as session:
        # Get API key (assuming one exists)
        api_key = "test_api_key"  # Replace with actual API key

        # Get CSRF token
        async with session.get(f"{BASE_URL}/api/csrf-token") as resp:
            data = await resp.json()
            csrf_token = data['csrf_token']

        # Create a test session
        print("Creating test session...")
        async with session.post(
            f"{BASE_URL}/api/sessions",
            params={"api_key": api_key},
            headers={
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/json"
            },
            json={"title": "Race Condition Test Session"}
        ) as resp:
            if resp.status != 200:
                print(f"Failed to create session: {resp.status}")
                print(await resp.text())
                return
            session_data = await resp.json()
            session_code = session_data['session_code']
            print(f"✓ Session created: {session_code}")

        # Test 1: Concurrent question submissions
        print("\n=== TEST 1: Concurrent Question Submissions ===")
        print("Submitting 10 questions concurrently...")

        async def submit_question(num):
            async with session.post(
                f"{BASE_URL}/api/sessions/{session_code}/questions",
                json={"text": f"Test question {num}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['question_number']
                else:
                    print(f"Question {num} failed: {resp.status}")
                    return None

        # Submit 10 questions concurrently
        start = time.time()
        tasks = [submit_question(i) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        print(f"Submitted 10 questions in {elapsed:.2f}s")
        print(f"Question numbers received: {sorted([r for r in results if r])}")

        # Verify no duplicates
        question_numbers = [r for r in results if r]
        if len(question_numbers) == len(set(question_numbers)):
            print("✅ No duplicate question numbers detected!")
        else:
            print("❌ DUPLICATE QUESTION NUMBERS DETECTED!")
            print(f"Expected: {list(range(1, 11))}")
            print(f"Got: {sorted(question_numbers)}")

        # Test 2: Concurrent vote submissions
        print("\n=== TEST 2: Concurrent Vote Submissions ===")
        print("Submitting 20 votes concurrently on question 1...")

        async def submit_vote():
            async with session.post(
                f"{BASE_URL}/api/questions/1/vote?action=add"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['upvotes']
                return None

        # Submit 20 votes concurrently
        start = time.time()
        tasks = [submit_vote() for _ in range(20)]
        vote_results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        print(f"Submitted 20 votes in {elapsed:.2f}s")
        final_votes = vote_results[-1] if vote_results else None
        print(f"Final vote count: {final_votes}")

        if final_votes == 20:
            print("✅ Vote count is correct (20)!")
        else:
            print(f"❌ VOTE COUNT INCORRECT! Expected 20, got {final_votes}")

        # Test 3: Rapid question numbering
        print("\n=== TEST 3: Rapid Sequential Submissions ===")
        print("Submitting 5 more questions rapidly...")

        results = []
        for i in range(11, 16):
            result = await submit_question(i)
            results.append(result)

        print(f"Question numbers: {results}")
        expected = list(range(11, 16))
        if results == expected:
            print(f"✅ Sequential numbering correct: {expected}")
        else:
            print(f"❌ SEQUENTIAL NUMBERING INCORRECT!")
            print(f"Expected: {expected}")
            print(f"Got: {results}")

        print("\n=== SUMMARY ===")
        print("✓ All race condition tests completed")

if __name__ == "__main__":
    print("Race Condition Test Suite")
    print("=" * 50)
    asyncio.run(create_session_and_test())
