# AI Prompts Log — HW4: Campus Customs

Log of prompts given to the AI coding assistant, organized by problem.

---

## Problem 1: Vibe coder prompts

1. > Working on hw4 today, put all my work there.

2. > Here is the context of hw4, which will be divided into 13 Problems
   >
   > I will build a customer website with a chatbot for Campus Customs ("CC"), using a React + Vite Typescript front end and a Python FastAPI backend whose brain is a PydanticAI agent
   >
   > I have placed a data folder in hw4 with campus_customs.db with product catalogue, inventory by size and users with hashed password. Refer to https://yalebulldogblue.com/ for the style of Campus Customs page and information
   >
   > Use my PORTKEY_API_KEY for AI calls
   >
   > Based on this, create requirements.txt with requirements you deem necessary/appropriate

3. > Starting with problem 1, create AI_prompts.md to log my prompts to you (AI). Create sections which include number and title as below. *(followed by the list of 13 problem titles)*

---

## Problem 2: Analyze the database

1. > Moving on to problem 2, open campus_customs.db for me so i can see the tables and data in there, mainly the catalogue, inventory and users

2. > Create output/harness.md
   >
   > Write down each table and the fields of each table, and short lines for why each field matters for the shop/chatbot
   >
   > We will continue growing the harness throughout hw4

---

## Problem 3: Build the Campus Customs website

1. > Moving on to problem 3, scaffold a React + Vite + TypeScript front end for CC. Put a nav bar at the top that links to main pages:
   >
   > * Home
   > * Products
   > * About Us
   > * Log in
   > * Create account
   >
   > Refer CC - style wording from the website I gave you, but write in own words and voice
   >
   > In the products page, show product images from catalogue (use image paths in database), include basic info such as name, price, short desc.
   >
   > Make each product open a single-item page (large image on left, full product text on the right with description, sizes, stock. Clicking a card in Products should take the viewer/shopper there
   >
   > Add  a chat interface in the bottom right of the site (floating chat panel). Does not need to talk to an agent yet, we will have a stub that will call a backend later
   >
   > Can start a simple FastAPI app in backend/main.py to serve products and images, and then we will it grow it into the agent backend

---

## Problem 4: Create account and login

1. > Moving on to problem 4. Build a create account/log in flow
   > Create account: first name, last name, email, password, confirm password
   > Log in: email and password
   >
   > All new accounts go into our 'users' table. Make sure to store passwords securely so hackers (human or AI) cannot access them

2. > Why cant i login with the test user:
   > email: test@campuscustoms.yale.edu
   > password: password

3. > I want to make sure the other existing users will be able to login later, other than the test user account

4. > I should be able to login with the test user [screenshot of login page showing "Incorrect email or password."]

5. > Do it for me

6. > Update output/harness.md with how authentication works (what is stored for a user and how passwords are protected). Then we will move on to problem 5


---

## Problem 5: PydanticAI agent backend

1. > Build the chatbot as a PydanticAI agent behind FastAPI plugged into my front end chat widget. Put the API app in backend/main.py, the file to run with Uvicorn. Keep the agent as four files next to it:
   > * backend/prompts/prompt.md
   > * backend/agent.py
   > * backend/tools.py
   > * backend/models.py
   >
   > in main.py, expose a chat route so a message from the website returns a reply from the agent (and everything needed for products/auth). Can use AI model API key, keep it safe though
   >
   > Put CC voice and safety basics into prompts/prompt.d. Start or update types in models.py for chat replies/product cards as needed
   >
   > in output/harness.md, discuss how the front end talks to FastAPI and how the agent is loaded (prompt file + model)
   >
   > Make sure the backend runs from backend/ folder likes this:
   > uvicorn main:app --reload --port 8000

---

## Problem 6: Tools: product info and stock

1. > Moving on to problem 6, give the agent tools that look up information from campus_customers.db:
   > * Product description
   > * Price
   > * how many are in stock (by size when the customer asks)
   >
   > Agent should use the database and not invent prices or quantities. If a size is out of stock, it must clearly state that
   >
   > Expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. Add or update return types in models.py
   >
   > In output/harness.md, list each tool and explain which model fields chosen for lookup results and why

---

## Problem 7: Chat search that updates the page

1. > Moving on to problem 7. When a customer asks about a type of item, the agent should search the catalogue and the website should dynamically show those matching items as product cards (image, name, price, short description)
   >
   > After the dynamic product cards are loaded, make sure the same single-item page behavior built in Problem 3 still works. Each product card, including the ones that the chat just put on the page, should still open that detail view (large image on left, full info on right) when clicked
   >
   > Update prompts/prompt.md and output/harness.md so its clear how search results reach the page

---

## Problem 8: Customer memory

1. > Moving on to problem 8. When a shopper logs in, save their chat history in the database in an appropriate table and reload it when they return. The agent should know who is chatting (name, email); put that in agent deps (or equivalent clear pattern) and/or tools the agent can call. Also pass enough page context that if someone is on a product page and asks "do you have this in pink" the agent knows which item they mean. Can put code into the agent context
   >
   > Guests should still be able to chat, but history only need to persist for logged-in users
   >
   > Document in output/harness.md how user chat history is stored, what customer fields the agent sees and how page context is passed

---

## Problem 9: Usability improvements

1. > Moving on to problem 9. Create output/usability.md
   >
   > Then recommend and implement 2 front-end usability improvements and 2 agent/backend usability improvements
   >
   > For each improvement, write in usability.md what was added and why it helps CC shopper or the business
   >
   > Make the improvements clearly visible & noticeable in the website when the app is run

---

## Problem 10: Style the website

1. > Moving on to problem 10. Implement a creative design so the site feels like a real CC storefront: fonts, color, hierarchy, motion, production presentation, chat feel. Make it ultra imaginative and innovative design, like really really push for this so that customers want to stay on the site
   >
   > Write output/design.md on what was changed and why it should help customers stick around and buy. Keep it concise

---

## Problem 11: Site testing (app check)

1. > Moving on to problem 11. Create output/app_check.html, a page you can double click to open
   >
   > I give you 3 screenshots. Add short captions for them. Basically they are:
   > 1. Check the inventory level of an item
   > 2. Dynamic search result cards appearing after a category question
   > 3. One of the usability features added, product page toolbar
   >
   > Make the HTML easy to review and grade: heading for each check, screenshot, one or two sentences on what the screenshot proves. Put the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths (e.g. app_check_images/inventory.png)

---

## Problem 12: Audit trail, safety, finish harness

1. > Moving on to problem 12. Keep an append-only output/audit_trail.json of agent-loop activity (time, tool name, shorts args/result, stop reason). Do not wipe it between runs. Also add safety rules to give to agent and put them in prompts/prompt.md
   >
   > Finish output/harness.md
   > * Model fields in models.py and why they were chosen
   > * Tools and abilities
   > * Safety rules
   > * Specs (loop limits, result caps, models, how to run front & back)

---

## Problem 13: Push to GitHub and submit the URL
