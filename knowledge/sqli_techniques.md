# Blind SQL Injection Techniques

## Overview

Blind SQL injection occurs when an application is vulnerable to SQL injection, but its HTTP responses do not contain the results of the SQL query or any database errors. This means you cannot directly see the data - instead, you must infer information based on the application's behavior.

## Conditional Responses

In conditional response blind SQLi, the application behaves differently depending on whether a SQL condition evaluates to TRUE or FALSE.

### Detection Pattern
1. Inject a condition that is always TRUE - observe response
2. Inject a condition that is always FALSE - observe response  
3. If responses differ, the application is vulnerable

### Example Detection
```sql
-- Always TRUE (should show normal response)
' AND '1'='1

-- Always FALSE (should show different response)
' AND '1'='2
```

## Extracting Data Character by Character

Since you cannot see query results directly, you must extract data one character at a time using conditional logic.

### Using SUBSTRING Function
The SUBSTRING function extracts a portion of a string:
```sql
SUBSTRING(string, start_position, length)
```

Example: `SUBSTRING('hello', 1, 1)` returns 'h'

### Character Comparison
Compare extracted characters to known values:
```sql
-- Check if first character of password is 'a'
' AND SUBSTRING(password,1,1)='a

-- Using ASCII for numeric comparison
' AND ASCII(SUBSTRING(password,1,1))>96
```

## Binary Search Optimization

Instead of testing each character (a-z, 0-9), use binary search on ASCII values:

### ASCII Ranges
- Lowercase letters: 97-122 (a-z)
- Uppercase letters: 65-90 (A-Z)
- Digits: 48-57 (0-9)
- Common special chars: 32-47, 58-64

### Binary Search Strategy
1. Test if ASCII value > midpoint
2. Narrow range based on result
3. Repeat until single character identified

Example for finding a character:
```sql
-- Is it > 'm' (ASCII 109)?
' AND ASCII(SUBSTRING(password,1,1))>109

-- If TRUE, test > 't' (ASCII 116)
-- If FALSE, test > 'f' (ASCII 102)
-- Continue halving until found
```

This reduces tests from ~36 (alphanumeric) to ~6 per character.

## Finding Password Length

Before extracting characters, determine the password length:
```sql
-- Is length > 10?
' AND LENGTH(password)>10

-- Binary search to find exact length
```

## Confirming Table and Column Existence

### Check Table Exists
```sql
' AND (SELECT COUNT(*) FROM users)>0--
```

### Check Column Exists  
```sql
' AND (SELECT COUNT(password) FROM users)>0--
```

## Working with Specific Users

If targeting a specific user (e.g., 'administrator'):
```sql
' AND SUBSTRING((SELECT password FROM users WHERE username='administrator'),1,1)='a
```

## Common Pitfalls

1. **Case sensitivity**: Database comparison may be case-sensitive
2. **Whitespace**: Extra spaces can break queries
3. **Comment syntax**: Use `--` or `#` appropriately for the database
4. **Quote escaping**: Match the quote style used in the application

## Response Indicators

Look for any difference between TRUE and FALSE conditions:
- Different page content (e.g., "Welcome back" message)
- Different response length
- Different HTTP status codes
- Different redirect behavior

## Systematic Approach

1. **Confirm vulnerability** - Verify TRUE/FALSE responses differ
2. **Identify target** - What data do you want to extract?
3. **Find length** - Determine length of target string
4. **Extract characters** - One by one, using binary search
5. **Verify** - Confirm extracted value is correct

