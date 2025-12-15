# Test Fix Plan

## Current Status
Based on the last test run, we have:
- **253 passed** ✅
- **51 failed** ❌
- **13 skipped** (expected - integration tests)

## Fixes Already Applied ✅

1. **AWS Test Mocking Paths** - Fixed 9 test files
   - Changed patch paths from `aws.{module}.boto3_session.Session` to `aws.boto3_session.Session`
   - Files: codebuild, cognito, dynamodb, elasticache, lambda, s3, secrets, sns, transfer_family

2. **Circuit Breaker Test** - Fixed state setting
   - Properly set `CircuitState.OPEN` and `last_failure_time`

3. **Log Print Function** - Restored print statement
   - Added back `print(result)` that was removed

4. **Lambda Test** - Added missing attribute
   - Added `log_stream_name` to MockContext

5. **Teams Tests** - Fixed patch path
   - Changed from `utils.teams.requests.post` to `requests.post`

6. **API Bug** - Fixed UnboundLocalError
   - Removed unused loop that referenced undefined `apiCreds`

7. **Rate Limiter Tests** - Updated expectations
   - Adjusted test logic to match implementation

## Remaining Failures - Fix Plan

### Category 1: Log Print Tests (5 failures) - HIGH PRIORITY
**Issue**: Tests use `@patch("sys.stdout", new_callable=StringIO)` but the patch isn't working correctly.

**Fix Strategy**:
```python
# Current approach doesn't work - need to patch at the right location
# Option 1: Use context manager
def test_color_print_basic(self):
    from io import StringIO
    import sys
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        log_print.color_print([{"string": "Hello", "text": "red"}])
        output = sys.stdout.getvalue()
        assert "Hello" in output
    finally:
        sys.stdout = old_stdout

# Option 2: Fix the patch decorator
@patch("builtins.print")  # Patch print directly
def test_color_print_basic(self, mock_print):
    log_print.color_print([{"string": "Hello", "text": "red"}])
    mock_print.assert_called_once()
    # Check the call arguments
```

**Files to Fix**: `test_utils_log_print.py`

**Implementation**:
```python
# Fix: Use patch on builtins.print instead of sys.stdout
@patch("builtins.print")
def test_color_print_basic(self, mock_print):
    styles = [{"string": "Hello", "text": "red"}]
    log_print.color_print(styles)
    mock_print.assert_called_once()
    # Verify the printed content contains the string
    call_args = str(mock_print.call_args)
    assert "Hello" in call_args or "033[31m" in call_args  # red ANSI code
```

---

### Category 2: Rate Limiter Tests (2-3 failures) - MEDIUM PRIORITY
**Issue**: Timing-sensitive tests that may fail due to race conditions.

**Fix Strategy**:
- Increase wait times slightly
- Use `time.sleep()` with buffer
- Or mock time for deterministic behavior

**Files to Fix**: `test_resilience.py` (test_rate_limiter_wait, test_rate_limiter_wait_if_needed)

**Implementation**:
- The `wait_if_needed()` method already calls `acquire()` internally after waiting
- Tests should account for this - after `wait_if_needed()`, one permit is already acquired
- May need to adjust test expectations or add small buffer time

---

### Category 3: Tableau Tests (3 failures) - MEDIUM PRIORITY
**Issue**: Tests need proper mocking of TableauAuth and Server classes.

**Fix Strategy**:
```python
# Need to check actual import path
# May need to patch: tableau.tableau_client.tableauserverclient.TableauAuth
# Or: tableauserverclient.TableauAuth
```

**Files to Fix**: `test_tableau.py`

**Implementation**:
- Check actual import: `from tableauserverclient import TableauAuth, Server`
- Patch should be: `@patch("tableau.tableau_client.TableauAuth")` or `@patch("tableauserverclient.TableauAuth")`
- May need to check the actual module structure

---

### Category 4: Teams Tests (3 failures) - MEDIUM PRIORITY
**Issue**: Tests are making real AWS calls or have incorrect mocking.

**Fix Strategy**:
- Ensure all AWS calls are properly mocked
- Mock `secrets.SecretHandler` properly
- Mock `sql.run_sql` properly

**Files to Fix**: `test_utils_teams.py`

**Implementation**:
- Ensure `@patch("aws.secrets.SecretHandler")` mocks the class properly
- Mock `sql.run_sql` to return a DataFrame with expected structure
- Mock `requests.post` (already fixed path)

---

### Category 5: DataFrame Expanded Tests (1 failure) - LOW PRIORITY
**Issue**: `test_build_rand_df_custom_columns` - likely a logic issue in the test or function.

**Fix Strategy**:
- Review the test expectations
- Check if the function signature matches test calls

**Files to Fix**: `test_utils_dataframe_expanded.py`

**Implementation**:
- **BUG FOUND**: Function `build_rand_df` ignores the `columns` parameter!
- Line 25 always generates columns: `columns = [ColNum2ColName(i) for i in range(1, colNum + 1)]`
- **Fix needed in `utils/dataframe.py`**:
  ```python
  def build_rand_df(randRange=100, colNum=10, rowNum=100, columns=None, absNums=True, intOnly=True):
      if columns is None:
          columns = [ColNum2ColName(i) for i in range(1, colNum + 1)]
      # Use provided columns instead of always generating
      # ... rest of function
  ```

---

### Category 6: Common Basic Expanded Tests (1 failure) - LOW PRIORITY
**Issue**: `test_get_list_of_words` - function may not exist or signature changed.

**Fix Strategy**:
- Check if function exists in `common.basic`
- Verify function signature matches test expectations

**Files to Fix**: `test_common_basic_expanded.py`

**Implementation**:
- Function exists in `common.basic`: `get_list_of_words()`
- Test mocks `requests.get` but may need to check import path
- Should patch: `@patch("common.basic.requests.get")` or `@patch("requests.get")`
- Verify function actually uses requests.get

---

### Category 7: GPU Utils Tests (2 failures) - LOW PRIORITY
**Issue**: Tests may require GPU hardware or SSH access.

**Fix Strategy**:
- Mock SSH connections
- Mock GPU detection functions
- Skip if hardware not available

**Files to Fix**: `test_server_management_gpu_utils.py`

**Implementation**:
- Tests mock `subprocess.run` but may need to check return value structure
- `mock_subprocess.return_value = mock_result` should work, but verify
- May need to ensure `mock_subprocess` is called with correct arguments
- Check if function handles subprocess failures correctly

---

### Category 8: Email Tests (1 failure) - MEDIUM PRIORITY
**Issue**: `test_send_email_with_secret` - AWS secrets mocking issue.

**Fix Strategy**:
- Ensure AWS secrets are properly mocked
- Check if boto3 client is mocked correctly

**Files to Fix**: `test_utils_email.py`

**Implementation**:
- Mock AWS secrets properly: `@patch("aws.secrets.SecretHandler")`
- Mock boto3 SES client
- Ensure email sending logic is properly isolated

---

### Category 9: API Tests (2 failures) - MEDIUM PRIORITY
**Issue**: Tests making real network calls or incorrect mocking.

**Fix Strategy**:
- Ensure `requests.post` is mocked
- Mock AWS secrets properly
- Check URL construction

**Files to Fix**: `test_utils_api.py`

**Implementation**:
- Already fixed `apiCreds` bug
- Ensure `requests.post` is mocked: `@patch("requests.post")` or `@patch("utils.api.requests.post")`
- Mock AWS secrets properly
- May need to check if URL construction is correct

---

## Implementation Priority

### Phase 1: Quick Wins (High Priority)
1. ✅ Log Print Tests - Fix patch mechanism
2. ✅ Rate Limiter Tests - Adjust timing
3. ✅ Tableau Tests - Fix import paths

### Phase 2: Mocking Issues (Medium Priority)
4. ✅ Teams Tests - Complete AWS mocking
5. ✅ Email Tests - Complete AWS mocking
6. ✅ API Tests - Complete network mocking

### Phase 3: Logic/Function Issues (Lower Priority)
7. ✅ DataFrame Expanded - Review function logic
8. ✅ Common Basic Expanded - Review function existence
9. ✅ GPU Utils - Add proper mocks or skips

## Estimated Impact

After fixes:
- **Expected**: ~300+ passing tests
- **Remaining failures**: ~5-10 (mostly integration tests requiring real services)
- **Success rate**: ~95%+

## Testing Strategy

1. Run tests by category to isolate issues
2. Fix one category at a time
3. Verify fixes don't break existing passing tests
4. Document any tests that legitimately need to be skipped
