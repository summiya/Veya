# Feature Specification

## 1. Instagram Connection

### Goal
Allow a creator to authorize Veya to access supported Instagram account data.

### Requirements
- Use the supported Meta/Instagram authorization flow.
- Store credentials securely.
- Never expose secrets to the frontend.
- Allow account disconnection.
- Handle expired or revoked tokens.

---

## 2. Media Import

### Goal
Retrieve media owned by the connected Instagram account.

### Requirements
- Retrieve posts and reels supported by the API.
- Store external media identifiers.
- Store only metadata required by Veya.
- Avoid duplicate records.
- Support pagination.

---

## 3. Comment Import

### Goal
Retrieve comments for owned media.

### Requirements
- Retrieve available comment text and metadata.
- Support pagination.
- Avoid duplicate ingestion.
- Handle removed or unavailable comments gracefully.
- Track the associated media item.

---

## 4. Sentiment Classification

### Goal
Classify comment sentiment efficiently.

### MVP labels
- Positive
- Neutral
- Negative

### Future labels
- Constructive feedback
- Toxic
- Severe abuse
- Spam

### Requirements
- Per-comment classification should use a dedicated NLP model.
- Store the resulting label and model confidence when available.
- Keep the model implementation behind an application-facing interface.
- Do not require an LLM call for each comment.

---

## 5. Profile Sentiment

### Goal
Give the creator an overall view of audience sentiment.

### Requirements
- Count analyzed comments.
- Calculate positive, neutral, and negative percentages.
- Percentages should be based only on successfully analyzed comments.
- Display the result in the React dashboard.

---

## 6. Post Sentiment

### Goal
Allow creators to compare audience response across posts.

### Requirements
- Calculate sentiment per media item.
- Show total comments analyzed.
- Show positive, neutral, and negative percentages.
- Provide a post details screen.

---

## 7. Positive Feed

### Phase
Post-MVP.

### Goal
Provide a view focused on supportive interactions.

### Requirements
- Show comments classified as positive.
- Allow filtering by post.
- Do not imply that negative feedback does not exist.

---

## 8. Comment Shield

### Phase
Post-MVP.

### Goal
Reduce unnecessary exposure to potentially harmful comments.

### Requirements
- Toxic text should not be displayed by default.
- Show aggregate counts without exposing the text.
- Allow the creator to deliberately reveal hidden comments.
- Maintain analytics even when comments are hidden from the interface.

---

## 9. AI Audience Summary

### Phase
Post-MVP.

### Goal
Turn large sets of comments into understandable themes.

### Example output
- What people loved
- Constructive feedback
- Recurring complaints
- Common questions

### Requirements
- Use an LLM only after comments have been filtered/grouped.
- Avoid sending unnecessary personal data.
- Keep the LLM provider behind an interface.
- Do not present generated summaries as exact quotations unless sourced from actual comments.
