import store

state = store.load()
draft_id = list(state["drafts"])[-1]
draft = state["drafts"][draft_id]
if draft["status"] != "rejected" or draft.get("facebook_post_id") or draft.get("instagram_media_id"):
    raise SystemExit("The last draft is not a rejected, unposted draft. Stopping.")
draft["status"] = "pending"
draft.pop("sent", None)
store.save(state)
print(f"Draft {draft_id} is pending again for testing.")