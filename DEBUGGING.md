# Debugging ra-mcp on Hugging Face

This guide helps debug timeout and API issues when deploying ra-mcp to Hugging Face Spaces.

## Environment Variables for Debugging

Set these in your Hugging Face Space settings:

### Required for Debugging

```bash
# Enable detailed logging (INFO level)
RA_MCP_LOG_LEVEL=INFO

# For maximum verbosity
RA_MCP_LOG_LEVEL=DEBUG
```

### Optional Configuration

```bash
# Enable API call logging to file (ra_mcp_api.log)
RA_MCP_LOG_API=1

# Override timeout (default: 60 seconds)
# Increase if Riksarkivet API is slow
RA_MCP_TIMEOUT=120
```

## Monitoring Logs on Hugging Face

### View Logs in Real-Time

1. Go to your Hugging Face Space
2. Click on "Logs" tab
3. Logs will show in real-time as requests come in

### What to Look For

The enhanced logging will show:

```
✓ Successful operations - marked with checkmarks
✗ Failed operations - marked with X
```

**Example successful search:**
```
INFO - ra_mcp.search_api - Starting search: keyword='Stockholm', max_docs=25, offset=0
INFO - ra_mcp.http_client - GET JSON: https://data.riksarkivet.se/api/records?transcribed_text=Stockholm&...
INFO - ra_mcp.http_client - ✓ GET JSON https://data.riksarkivet.se/api/records... - 1.234s - 45678 bytes - 200 OK
INFO - ra_mcp.search_api - ✓ Search completed: 25 hits from 100 total
```

**Example timeout:**
```
ERROR - ra_mcp.http_client - ✗ TIMEOUT after 60.000s on https://data.riksarkivet.se/api/records
ERROR - ra_mcp.http_client - Timeout limit was 60s
ERROR - ra_mcp.search_api - ✗ Search failed for keyword 'Stockholm': Exception: Request timeout
```

## Common Issues and Solutions

### 1. Timeout on Search

**Symptom:**
```
ERROR - ✗ TIMEOUT after 60.000s
```

**Solutions:**
- Increase timeout: Set `RA_MCP_TIMEOUT=120` in Space settings
- Reduce result size: Search with smaller `max_results` parameter
- Check Riksarkivet API status: Visit https://data.riksarkivet.se/api/records directly

### 2. Connection Errors

**Symptom:**
```
ERROR - URL Error: Name or service not known
```

**Solutions:**
- Check Hugging Face Space internet connectivity
- Verify Riksarkivet APIs are accessible from HF infrastructure
- Check if Riksarkivet is blocking HF IP addresses

### 3. Slow Response Times

**Symptom:**
```
INFO - ✓ GET JSON ... - 45.678s - 200 OK
```

**Solutions:**
- Normal response should be 1-5 seconds
- If >30s, consider:
  - Using simpler search terms
  - Reducing max_results
  - Checking Riksarkivet API load

## Debugging Steps

### Step 1: Enable Full Logging

In Hugging Face Space settings:
```
RA_MCP_LOG_LEVEL=DEBUG
RA_MCP_LOG_API=1
```

### Step 2: Test Basic Connectivity

Make a simple search request and check logs for:
1. "HTTPClient initialized" - confirms client setup
2. "GET JSON: https://data.riksarkivet.se..." - confirms request sent
3. "Connection established, status: 200" - confirms connection
4. "Received X bytes" - confirms data transfer
5. "✓ Search completed" - confirms success

### Step 3: Analyze Timing

Look for timing information in logs:
```
INFO - ✓ GET JSON ... - 1.234s - 200 OK
```

- **< 5s**: Normal
- **5-30s**: Slow but acceptable
- **> 30s**: Investigate Riksarkivet API or network
- **Exactly 60s + timeout**: Confirm timeout setting

### Step 4: Check Error Messages

All errors are logged with context:
```
ERROR - ✗ GET JSON https://... - 60.123s - TimeoutError: timeout
```

Error types:
- `TimeoutError`: Request took too long (increase `RA_MCP_TIMEOUT`)
- `HTTPError 5XX`: Riksarkivet server issue (retry later)
- `HTTPError 4XX`: Bad request (check search parameters)
- `URLError`: Network/DNS issue (check connectivity)

## Testing Locally Before Deployment

### Run with Same Configuration

```bash
# Set environment variables
export RA_MCP_LOG_LEVEL=DEBUG
export RA_MCP_LOG_API=1
export RA_MCP_TIMEOUT=120

# Run server
uv run ra serve --http

# Test search
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_transcribed",
      "arguments": {
        "keyword": "Stockholm",
        "offset": 0,
        "max_results": 10
      }
    }
  }'
```

Watch stderr for detailed logs.

## Log Levels Explained

- **DEBUG**: Everything (HTTP headers, parameters, step-by-step execution)
- **INFO**: High-level operations (requests, responses, timing)
- **WARNING**: Unusual but not critical issues
- **ERROR**: Failures that prevent operations

## Performance Optimization

### For Hugging Face Deployment

1. **Increase Timeout**:
   ```
   RA_MCP_TIMEOUT=120
   ```

2. **Use INFO Logging** (not DEBUG):
   ```
   RA_MCP_LOG_LEVEL=INFO
   ```
   - DEBUG creates too much output
   - INFO shows request/response timing

3. **Monitor Response Sizes**:
   - Large responses (>1MB) may be slow
   - Reduce `max_results` if needed

## Example Debugging Session

### Scenario: Timeouts on Hugging Face

1. **Enable logging:**
   ```
   RA_MCP_LOG_LEVEL=INFO
   RA_MCP_TIMEOUT=120
   ```

2. **Make test request**

3. **Check logs** for:
   ```
   INFO - Starting search: keyword='test'
   INFO - GET JSON: https://data.riksarkivet.se/...
   INFO - Opening connection to https://data.riksarkivet.se...
   ```

4. **If timeout occurs at "Opening connection":**
   - Network/connectivity issue
   - Check Hugging Face → Riksarkivet connectivity

5. **If timeout occurs at "Reading response content":**
   - Large response or slow API
   - Increase `RA_MCP_TIMEOUT`
   - Reduce `max_results`

## Contact & Support

If issues persist:
1. Check logs with `RA_MCP_LOG_LEVEL=DEBUG`
2. Save full log output
3. Open GitHub issue with:
   - Error messages
   - Timing information
   - Search parameters used
   - Hugging Face Space configuration

## Additional Resources

- **Riksarkivet API Status**: https://data.riksarkivet.se/api/records
- **HTTP Client Code**: [src/ra_mcp/utils/http_client.py](src/ra_mcp/utils/http_client.py)
- **Search Client Code**: [src/ra_mcp/clients/search_client.py](src/ra_mcp/clients/search_client.py)
- **MCP Server Code**: [src/ra_mcp/server.py](src/ra_mcp/server.py)
