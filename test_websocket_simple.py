#!/usr/bin/env python3
"""
Simple WebSocket security test - tests invalid session rejection.
"""

import asyncio
import sys
from websockets import connect, exceptions

BASE_URL = "ws://localhost:8000"


async def test_invalid_session():
    """Test that invalid session codes are rejected."""
    print("Testing invalid session code rejection...")

    try:
        import json
        websocket = await connect(f"{BASE_URL}/ws/INVALID_SESSION_CODE_12345", timeout=5)
        print("   Connected to WebSocket")

        # Should receive an error message
        try:
            msg = await asyncio.wait_for(websocket.recv(), timeout=3)
            data = json.loads(msg)
            print(f"   Received message: type={data.get('type')}, message={data.get('message')}")

            if data.get('type') == 'error' and 'not found' in data.get('message', '').lower():
                print("   ✓ Correct error message received")

            # Now wait for connection to close
            try:
                await asyncio.wait_for(websocket.recv(), timeout=2)
                print("❌ FAILED: Should not receive second message")
                return False
            except exceptions.ConnectionClosed as e:
                print(f"✅ PASSED: Connection closed by server")
                print(f"   Close code: {e.code}, Reason: {e.reason}")
                if e.code == 4004:
                    print("   ✓ Correct close code (4004 - Session not found)")
                return True

        except asyncio.TimeoutError:
            print("❌ FAILED: Timeout waiting for error message")
            await websocket.close()
            return False
        except exceptions.ConnectionClosed as e:
            print(f"✅ PASSED: Connection closed immediately")
            print(f"   Close code: {e.code}, Reason: {e.reason}")
            return True

    except exceptions.ConnectionClosed as e:
        print(f"✅ PASSED: Connection closed during handshake")
        print(f"   Close code: {e.code}, Reason: {e.reason}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {type(e).__name__}: {e}")
        return False


async def main():
    """Run WebSocket security test."""
    print("=" * 60)
    print("WebSocket Security Test - Invalid Session Rejection")
    print("=" * 60)
    print()

    result = await test_invalid_session()

    print()
    print("=" * 60)
    if result:
        print("✅ Test PASSED")
        sys.exit(0)
    else:
        print("❌ Test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
