#!/usr/bin/env python
"""
Test script to measure IIIF API response times with different HTTP clients.
"""

import time
import requests
import subprocess
import json
from urllib.request import urlopen

def test_requests_library():
    """Test with Python requests library."""
    url = "https://lbiiif.riksarkivet.se/collection/arkiv/zhTCkvvgwALOVWzN3BYLBF"

    print("=" * 60)
    print("Testing with requests library")
    print("=" * 60)

    for timeout in [5, 10, 30, 60]:
        print(f"\nTimeout: {timeout}s")
        start = time.time()

        try:
            response = requests.get(url, timeout=timeout)
            elapsed = time.time() - start

            print(f"  Status Code: {response.status_code}")
            print(f"  Content Length: {len(response.content)} bytes")
            print(f"  Time taken: {elapsed:.2f}s")

            # Try to parse JSON
            data = response.json()
            print(f"  JSON parsed successfully")
            print(f"  Keys: {list(data.keys())}")
            if 'items' in data:
                print(f"  Items count: {len(data['items'])}")

            break  # Success, no need to try longer timeouts

        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            print(f"  TIMEOUT after {elapsed:.2f}s")

        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start
            print(f"  CONNECTION ERROR after {elapsed:.2f}s")
            print(f"  Error: {e}")

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ERROR after {elapsed:.2f}s")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error: {e}")

def test_requests_with_session():
    """Test with requests Session (what the app uses)."""
    url = "https://lbiiif.riksarkivet.se/collection/arkiv/zhTCkvvgwALOVWzN3BYLBF"

    print("\n" + "=" * 60)
    print("Testing with requests.Session()")
    print("=" * 60)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Transcribed-Search-Browser/1.0",
        "Accept-Encoding": "gzip, deflate",
    })

    for timeout in [5, 10, 30, 60]:
        print(f"\nTimeout: {timeout}s")
        start = time.time()

        try:
            response = session.get(url, timeout=timeout)
            elapsed = time.time() - start

            print(f"  Status Code: {response.status_code}")
            print(f"  Content Length: {len(response.content)} bytes")
            print(f"  Time taken: {elapsed:.2f}s")

            # Try to parse JSON
            data = response.json()
            print(f"  JSON parsed successfully")
            print(f"  Keys: {list(data.keys())}")
            if 'items' in data:
                print(f"  Items count: {len(data['items'])}")

            break  # Success, no need to try longer timeouts

        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            print(f"  TIMEOUT after {elapsed:.2f}s")

        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start
            print(f"  CONNECTION ERROR after {elapsed:.2f}s")
            print(f"  Error: {e}")

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ERROR after {elapsed:.2f}s")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error: {e}")

def test_requests_streaming():
    """Test with streaming mode."""
    url = "https://lbiiif.riksarkivet.se/collection/arkiv/zhTCkvvgwALOVWzN3BYLBF"

    print("\n" + "=" * 60)
    print("Testing with requests streaming mode")
    print("=" * 60)

    for timeout in [5, 10, 30, 60]:
        print(f"\nTimeout: {timeout}s")
        start = time.time()

        try:
            with requests.get(url, timeout=timeout, stream=True) as response:
                elapsed_headers = time.time() - start
                print(f"  Headers received in {elapsed_headers:.2f}s")
                print(f"  Status Code: {response.status_code}")

                # Try to read content
                content = response.content
                elapsed = time.time() - start

                print(f"  Content Length: {len(content)} bytes")
                print(f"  Total time: {elapsed:.2f}s")

                # Try to parse JSON
                data = json.loads(content)
                print(f"  JSON parsed successfully")
                print(f"  Keys: {list(data.keys())}")
                if 'items' in data:
                    print(f"  Items count: {len(data['items'])}")

                break  # Success

        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            print(f"  TIMEOUT after {elapsed:.2f}s")

        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start
            print(f"  CONNECTION ERROR after {elapsed:.2f}s")
            print(f"  Error: {e}")

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ERROR after {elapsed:.2f}s")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error: {e}")

def test_curl():
    """Test with curl command."""
    url = "https://lbiiif.riksarkivet.se/collection/arkiv/zhTCkvvgwALOVWzN3BYLBF"

    print("\n" + "=" * 60)
    print("Testing with curl")
    print("=" * 60)

    for timeout in [5, 10, 30, 60]:
        print(f"\nTimeout: {timeout}s")
        start = time.time()

        try:
            result = subprocess.run(
                ["curl", "-s", "-m", str(timeout), url],
                capture_output=True,
                text=True,
                timeout=timeout + 2  # Give curl a bit more time
            )
            elapsed = time.time() - start

            if result.returncode == 0:
                content = result.stdout
                print(f"  Content Length: {len(content)} bytes")
                print(f"  Time taken: {elapsed:.2f}s")

                # Try to parse JSON
                data = json.loads(content)
                print(f"  JSON parsed successfully")
                print(f"  Keys: {list(data.keys())}")
                if 'items' in data:
                    print(f"  Items count: {len(data['items'])}")

                break  # Success
            else:
                print(f"  curl failed with return code: {result.returncode}")
                print(f"  Time taken: {elapsed:.2f}s")
                if result.stderr:
                    print(f"  Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            print(f"  TIMEOUT after {elapsed:.2f}s")

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ERROR after {elapsed:.2f}s")
            print(f"  Error: {e}")

def test_urllib():
    """Test with urllib (standard library)."""
    url = "https://lbiiif.riksarkivet.se/collection/arkiv/zhTCkvvgwALOVWzN3BYLBF"

    print("\n" + "=" * 60)
    print("Testing with urllib")
    print("=" * 60)

    for timeout in [5, 10, 30, 60]:
        print(f"\nTimeout: {timeout}s")
        start = time.time()

        try:
            with urlopen(url, timeout=timeout) as response:
                content = response.read()
                elapsed = time.time() - start

                print(f"  Status Code: {response.status}")
                print(f"  Content Length: {len(content)} bytes")
                print(f"  Time taken: {elapsed:.2f}s")

                # Try to parse JSON
                data = json.loads(content)
                print(f"  JSON parsed successfully")
                print(f"  Keys: {list(data.keys())}")
                if 'items' in data:
                    print(f"  Items count: {len(data['items'])}")

                break  # Success

        except TimeoutError:
            elapsed = time.time() - start
            print(f"  TIMEOUT after {elapsed:.2f}s")

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ERROR after {elapsed:.2f}s")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error: {e}")

def main():
    """Run all tests."""
    print("Testing IIIF API response times")
    print(f"URL: https://lbiiif.riksarkivet.se/collection/arkiv/zhTCkvvgwALOVWzN3BYLBF")
    print()

    # Test different methods
    test_curl()  # Start with curl since it usually works
    test_urllib()
    test_requests_library()
    test_requests_with_session()
    test_requests_streaming()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("If curl succeeds but requests fails, it's likely an issue with")
    print("how Python's requests library handles the SSL/TLS connection or")
    print("the response streaming from this particular server.")

if __name__ == "__main__":
    main()