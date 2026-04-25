# Session & Cookies Teaching Plan

Total time: ~75 minutes

## Part 1: The Problem (5 min)

**Where:** Whiteboard / verbal

Ask the class: "If I send two requests to a server, does the server know they came from the same person?" No. HTTP is stateless. Every request is a stranger.

Then ask: "So how does YouTube know you're logged in when you click from video to video?" That's what we're building today.

Three problems to solve:
- Where do we store users? (database)
- How does the server remember you? (sessions)
- How does the browser prove it's you? (cookies)


## Part 2: Database + Models (10 min)

**Where:** Notebook cells — Step 1 and Step 2

Run the cells. Show the empty tables. Explain:
- users table = WHO exists
- sessions table = WHO is currently logged in
- They're separate. You can exist without being logged in.

Point at the ASCII table diagram in Step 2. Ask: "What connects the sessions table to the users table?" Answer: user_id.


## Part 3: Signup (5 min)

**Where:** Notebook cells — Step 3

Run the signup cell. Then run the inspect cell.

Key moment: show the users table has rows but sessions table is still empty. Say: "Priya exists but she's NOT logged in. There's no session, no cookie. The server has no idea she's here."


## Part 4: Login — the core lesson (15 min)

**Where:** Notebook cells — Step 4

This is the most important part. Go slow.

Run the login cell line by line (or explain each print statement as it appears):
1. Found user in DB
2. Generated random token — point out it's 64 characters, ask "could you guess this?"
3. Saved to sessions table — "now the server knows this token belongs to Priya"
4. Set-Cookie header — "this is what the browser receives"

Then run the inspect cell. Show both tables side by side. Ask: "What's the connection between the cookie the browser holds and the database?" The token value is the same string in both places.

Draw on whiteboard:
```
Browser cookie: "a6f3b9..."  ←──── same value ────→  sessions.session_token: "a6f3b9..."
                                                      sessions.user_id: 1
                                                                ↓
                                                      users.id: 1 → Priya
```


## Part 5: Reading the session (10 min)

**Where:** Notebook cells — Step 5

Run the /auth/me simulation. Walk through each step printed in the output.

Then ask: "What if Priya closes her browser and opens it again tomorrow? Does she need to login again?" It depends on whether the cookie is still there and whether the session expired.

Then ask: "What if I send a request without a cookie?" Don't answer, show them.


## Part 6: Security — fake cookie + HttpOnly (10 min)

**Where:** Notebook cell Step 6 + Browser DevTools

Run the fake cookie cell. Let them see "NOT FOUND in database." Explain: "You can't forge a session because you can't guess a 64-character random string. There are more possible tokens than atoms in the universe."

Then switch to Swagger UI (localhost:8000/docs). Do this live:
1. POST /auth/signup with a new user
2. POST /auth/login — point at the Set-Cookie in response headers
3. Open DevTools → Application → Cookies → show the cookie appeared
4. Open Console → type `document.cookie` → empty string
5. Say: "The cookie is there but JavaScript can't read it. That's HttpOnly. Even if someone injects malicious code into our page, they can't steal this cookie."


## Part 7: Multiple sessions (5 min)

**Where:** Notebook cells — Step 7

Run the cell. Show two rows in the sessions table, both with user_id=1.

Ask: "If Priya logs out on her laptop, should her phone also get logged out?" Let them debate. Then run the verify cell showing both tokens work independently.

Real world example: "This is why when you change your Google password, it gives you the option to sign out of all other devices. That means deleting ALL session rows for that user_id."


## Part 8: Logout (5 min)

**Where:** Notebook cells — Step 8

Run the logout cell. Show:
- Token A is gone from the DB
- Token B still works
- Even if someone copied Token A before logout, it's dead now

Say: "Logout = two deletes. Delete from the database so the server forgets. Clear the cookie so the browser forgets. Both sides."


## Part 9: Gatekeeper / Depends (5 min)

**Where:** Notebook cells — Step 10

Run the gatekeeper simulation. Three tests print one after another:
1. No cookie → rejected at step 1
2. Fake cookie → rejected at step 2
3. Valid cookie → all 4 steps pass, access granted

Say: "This function runs BEFORE your chat endpoint. If it fails, your code never executes. Your OpenAI credits are safe."


## Part 10: Live Swagger demo (10 min)

**Where:** Browser — localhost:8000/docs

If the server isn't running, start it:
```
python -m uvicorn app:app --reload --port 8000
```

Walk through these in order. Let students follow along if they have the project:

1. POST /auth/signup → `{"email":"neha@test.com","name":"Neha Kapoor"}` → 200
2. POST /auth/login → `{"email":"nobody@fake.com"}` → 404 (user not found)
3. POST /auth/login → `{"email":"neha@test.com"}` → 200 (check cookies tab, cookie appeared)
4. GET /auth/me → 200 returns Neha's info (you didn't type credentials, the cookie did it)
5. POST /chat → `{"question":"What is 5+5?"}` → works, agent answers
6. Edit cookie value in DevTools to garbage → GET /auth/me → 401
7. Fix it: POST /auth/login again → cookie refreshed
8. POST /auth/logout → cookie gone from DevTools
9. POST /chat → 401 (no cookie, blocked)
10. Console tab → `document.cookie` → "" (HttpOnly proof)


## Part 11: The bridge to Google OAuth (2 min)

**Where:** Notebook — last cell + verbal

Show the last cell. Read the comparison table.

Say: "Everything we built today is real production auth. The session, cookie, gatekeeper — that's all staying. The only problem is we trusted the email without checking. Phase 2: we let Google verify the identity, then we do the exact same session creation. The plumbing doesn't change."


## Quick reference: where to teach what

| Topic | Where to show it |
|-------|-----------------|
| What a session token looks like | Notebook Step 4 output |
| What's stored in the database | Notebook inspect cells (run after each step) |
| What a cookie header looks like | Swagger UI response headers |
| HttpOnly proof | Browser Console: `document.cookie` |
| Cookie appearing/disappearing | Browser DevTools → Application → Cookies |
| Fake cookie attack | Notebook Step 6 + edit cookie in DevTools |
| Protected route blocking | Swagger: /chat without cookie → 401 |
| Multiple sessions | Notebook Step 7 |
| Logout cleanup | Notebook Step 8 + Swagger POST /auth/logout |
| Full flow end to end | Frontend at localhost:5173 (signup → chat → logout) |
