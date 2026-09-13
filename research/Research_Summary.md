# Research Notes — Adobe University Hackathon 2026, Round 3

## Why we did this research

For Round 3, Adobe wanted us to turn the ideas from Round 2 into reusable Agent Skills. The main problem is not just SEO. The marketplace needs to look at why a website may be difficult for AI systems to find and understand, and also why a visitor may leave after reaching the site.

We used research from the web and our own testing to decide which signals were worth turning into actual checks.

The basic approach was:

**What we noticed → what can be checked on any website → what evidence proves it → which skill should handle it.**

---

## 1. Getting important content to the crawler

One of the first things we looked at was the basic question: **can a machine actually reach the information?**

A page can look perfectly normal in a browser but still have problems from a crawler's point of view. Things such as blocked pages, broken links, HTTP errors, poor internal linking, missing sitemap information, canonical problems, or content that only appears after JavaScript runs can all make useful information harder to discover.

This led us to the following rule:

> Important content needs to be reachable and readable, not just visible to a human using a browser.

### Where this appears in our project

This became part of the **Crawl & Render Audit**.

It checks things including:

- robots.txt
- sitemap discovery
- HTTP errors
- canonical URLs
- internal links
- page metadata
- rendered versus non-rendered content
- important page types

We also added limits for requests, runtime, and rendered pages so that the crawler stays controlled.

---

## 2. Making page information easy to understand

We also looked at how pages are structured. Clear titles, headings, links and semantic information make it easier to understand what a page is about.

This is useful for both people and automated readers.

The practical idea we took from this was:

> Important information should be stated clearly instead of making the reader infer it from the design.

For our audit, this means looking at page structure, metadata, headings, visible content and other signals that help identify what a page contains.

This work is mainly handled by the **Crawl & Render Audit**, with some of the more AI-focused checks handled by the **AI Discoverability Audit**.

---

## 3. Structured information should agree with what people see

This became one of the more useful areas of the research.

Websites can provide information in structured formats such as Schema.org JSON-LD. For example, a product page can contain a product name, organization, offer and price in structured data.

The important point is that the structured information should not contradict the actual page.

For example:

```text
Structured data:  Product A — ₹999
Visible page:     Product A — ₹1,299
```

This is a more meaningful problem than simply saying that JSON-LD is missing.

So we implemented checks that compare important structured facts with visible facts.

### Where this appears

**AI Discoverability Audit**

It looks at things such as:

- product information
- prices
- organization identity
- visible versus structured facts
- answerability

This also feeds into our **Evidence Graph**.

---

## 4. Connecting products, prices and organizations

While looking at structured data, we also looked at how products and offers are represented.

A product is not an isolated piece of text. There can be a relationship between:

- the product
- its price or offer
- the organization providing it

That led us to model some of these relationships explicitly.

For example:

```text
Page
  └── declares → Product
                  └── has_price → ₹999
```

This makes it easier to spot cases where a product or price is inconsistent.

The implementation is split between the **AI Discoverability Audit** and the **Evidence Graph**.

---

## 5. Keeping brand and entity information consistent

Another area we focused on was identity.

A website can mention the same company, product or service in many places. If the name or important facts change between pages, it becomes harder to tell whether all of the information refers to the same entity.

So our general rule became:

> Important entities should have a consistent identity across the site.

We added checks for organization names, entity references and conflicting facts. The Evidence Graph helps connect these pieces instead of treating each one as an unrelated warning.

This is covered mainly by the **Freshness & Corroboration** and **AI Discoverability** parts of the marketplace.

---

## 6. Freshness and conflicting information

Some website information simply goes out of date.

We therefore looked at signals around freshness and corroboration, especially for facts that could affect how a brand is described.

The useful distinction here is between:

- information that is present,
- information that is current,
- and information that agrees with other available evidence.

This became the **Freshness & Corroboration** skill.

It checks for stale information, conflicting facts and entity ambiguity.

We also kept external corroboration optional. The core audit does not need an outside service to work.

---

## 7. What happens after someone reaches the site?

The second half of Adobe's problem is engagement.

A website can be easy for an AI system to discover but still be difficult for a person to use. We therefore looked at whether a visitor can quickly answer questions such as:

- Where am I?
- What does this page/site offer?
- Why should I trust it?
- What should I look at next?
- What action can I take?

This led to checks around page orientation, navigation, context, calls to action, trust information and decision-support information.

These checks are handled by the **Engagement Audit**.

---

## 8. Thinking about the whole referral journey

We did not want the final report to stop at "the visitor reached the website."

We modelled the journey as:

```text
Discovery
   ↓
Understanding
   ↓
Trust
   ↓
Decision
   ↓
Conversion
```

A site may be strong at one stage and weak at another.

For example, a product could be easy to discover but have poor information for making a purchase decision.

We turned this idea into the **AI Referral Journey** in the orchestrator. It groups evidence by stage and can highlight where the main bottleneck appears to be.

---

## 9. Showing why a finding was produced

During development, we found that a list of warnings is not enough. It is much more useful when the relationship between the page and the evidence is clear.

That is why we added the **Evidence Graph**.

A simplified example is:

```text
Page
  ├── declares → Product
  ├── shows_visible_fact → Product
  └── Product → has_price → ₹999
```

If another representation says ₹1,299, the graph can represent the conflict.

This gives the final report more context and helps us avoid treating isolated signals as definite problems.

---

## 10. Prioritizing the recommendations

Adobe asks for suggested actions and expects them to be prioritized.

We did not want the report to produce twenty findings with no indication of what should be fixed first.

Our action ranking takes into account things such as:

- severity
- confidence
- expected impact
- implementation effort
- category of the issue

The result is an **Impact × Effort style ranking** so a team can start with the changes that are likely to matter most.

---

## 11. Designing for websites we have never seen

This was an important part of the research because Adobe evaluates the marketplace on unseen websites.

We therefore avoided rules tied to one particular brand.

For example, we do not want a rule like:

```text
If this is Brand X, look for Y.
```

Instead, we use rules such as:

```text
If an important product fact differs between
structured data and visible content, report the mismatch
with the supporting evidence.
```

That type of rule can work on different websites.

We reinforced this with generalized fixtures, adversarial tests and adaptive crawling.

---

## 12. Research and implementation map

| What we learned | What we check | Where it is implemented |
|---|---|---|
| Machines need to reach useful pages | Crawlability and readability | Crawl & Render Audit |
| Clear page structure helps interpretation | Titles, headings, metadata and content structure | Crawl & Render Audit |
| Structured data can describe important facts | Machine-readable product/org information | AI Discoverability Audit |
| Structured and visible facts should agree | Product and price consistency | AI Discoverability Audit |
| Products, offers and providers are related | Product → offer → organization relationships | AI Discoverability + Evidence Graph |
| Entity identity should stay consistent | Names and factual consistency | Freshness + AI Discoverability |
| Important information can become stale | Freshness signals | Freshness & Corroboration |
| Facts can conflict | Conflict/corroboration checks | Freshness + Evidence Graph |
| Visitors need clear orientation | Navigation, context and page clarity | Engagement Audit |
| Engagement continues after discovery | Discovery → conversion stages | AI Referral Journey |
| Findings should be explainable | Evidence relationships | Evidence Graph |
| Fixes need an order | Impact, effort, severity and confidence | Action Ranking |
| The evaluator will use unseen sites | Generalized patterns rather than site-specific rules | Whole Marketplace |

---

## 13. Main conclusion from the research

The main thing we took away is that **AI readiness is not just about adding structured data or making a site crawlable**.

A useful website needs to be:

- reachable,
- readable,
- understandable,
- consistent,
- current,
- easy to navigate,
- and useful after the visitor arrives.

That is why the final marketplace combines technical auditing with discoverability, engagement, evidence and recommendation layers.

---

## 14. What we deliberately did not add

We decided not to turn this into a general-purpose SEO platform or website editor.

We did not add:

- automatic website changes
- CMS editing
- deployment
- authenticated site modifications
- a dependency on a proprietary AI API
- pretrained model weights
- a database of brand-specific rules

Those additions would increase the size of the project without directly helping the Round 3 objective.

---

## 15. Final research status

The research phase is now complete.

The useful observations have been converted into checks and then into the marketplace architecture.

At this point, more research would have diminishing returns. The better use of time is to test the final marketplace, prepare the demo, and explain the connection between the research and the implementation.

