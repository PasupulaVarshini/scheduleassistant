"""
Agentic RAG Engine for Schedule Assistant.
Implements:
1. Tool: get_schedule (semantic vector retrieval + temporal/metadata filtering + availability analysis)
2. Tool: update_schedule (adds, updates, moves, removes events with real-time vector re-indexing)
3. Autonomous reasoning loop with transparent execution traces
"""
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple

from vector_store import ScheduleVectorStore


def parse_relative_date(date_str: str, base_date: date) -> Optional[date]:
    """Resolves natural language dates relative to base_date."""
    if not date_str:
        return None
    s = date_str.lower().strip()

    if "today" in s:
        return base_date
    if "tomorrow" in s:
        return base_date + timedelta(days=1)
    if "day after tomorrow" in s:
        return base_date + timedelta(days=2)
    if "yesterday" in s:
        return base_date - timedelta(days=1)

    # Check for weekday names (e.g. "friday", "this friday", "next monday")
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for idx, day_name in enumerate(weekdays):
        if day_name in s:
            current_weekday = base_date.weekday()
            days_ahead = (idx - current_weekday) % 7
            if days_ahead == 0 and "next" in s:
                days_ahead = 7
            elif days_ahead == 0 and "today" not in s:
                # If target day is today but user said day name, usually means today or next week
                pass
            return base_date + timedelta(days=days_ahead)

    # Check for month names like "august 15", "aug 15", "october 14"
    months = {
        "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
        "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
        "august": 8, "aug": 8, "september": 9, "sep": 9, "october": 10, "oct": 10,
        "november": 11, "nov": 11, "december": 12, "dec": 12
    }

    month_match = re.search(r"\b([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\b", s)
    if month_match:
        m_name = month_match.group(1).lower()
        day_num = int(month_match.group(2))
        if m_name in months:
            m_num = months[m_name]
            target_year = base_date.year
            try:
                candidate = date(target_year, m_num, day_num)
                # If user specifies date in past, keep current year or next
                return candidate
            except ValueError:
                pass

    # Direct ISO format YYYY-MM-DD
    iso_match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", s)
    if iso_match:
        try:
            return datetime.strptime(iso_match.group(0), "%Y-%m-%d").date()
        except Exception:
            pass

    return None


def parse_time_str(time_str: str) -> Optional[str]:
    """Converts '3 PM', '14:00', '10:30 am' to 'HH:MM' 24-hr format."""
    if not time_str:
        return None
    s = time_str.lower().strip()

    # Match "3 PM", "3:30 pm", "11:15 AM", "2pm"
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", s)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    # Match standard 24-hour HH:MM
    m24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", s)
    if m24:
        return f"{int(m24.group(1)):02d}:{m24.group(2)}"

    return None


class ScheduleAgent:
    def __init__(self, vector_store: ScheduleVectorStore, base_date: date = None):
        self.vector_store = vector_store
        self.base_date = base_date or date.today()

    def set_base_date(self, new_base: date):
        self.base_date = new_base

    # --------------------------------------------------------------------------
    # TOOL 1: get_schedule
    # --------------------------------------------------------------------------
    def get_schedule(
        self,
        query: str = "",
        target_date: Optional[str] = None,
        time_of_day: Optional[str] = None,
        category: Optional[str] = None,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Tool 1: Retrieves relevant schedule information based on date, time, or user query.
        Uses ChromaDB vector similarity search combined with temporal slot analysis.
        """
        # If target_date is given, get all events for that exact date directly
        exact_date_events = []
        if target_date:
            all_evts = self.vector_store.list_all_events()
            exact_date_events = [e for e in all_evts if e.get("date") == target_date]

        # Semantic RAG search via ChromaDB
        search_query = query if query.strip() else (f"events on {target_date}" if target_date else "upcoming events")
        rag_results = self.vector_store.query_rag(
            query_text=search_query,
            n_results=n_results,
            date_filter=target_date if target_date else None,
            category_filter=category
        )

        # Merge exact date events with RAG matches
        merged_ids = set()
        combined_events = []

        # If date query, prioritize chronological events of that date
        if target_date:
            for e in exact_date_events:
                if e["id"] not in merged_ids:
                    merged_ids.add(e["id"])
                    combined_events.append(e)

        for r in rag_results:
            if r["id"] not in merged_ids:
                merged_ids.add(r["id"])
                combined_events.append(r)

        # If time_of_day filter applies (e.g. afternoon: 12:00 - 18:00)
        filtered_events = []
        time_slot_label = ""
        if time_of_day:
            tod = time_of_day.lower()
            if "afternoon" in tod:
                time_slot_label = "Afternoon (12:00 PM – 5:00 PM)"
                start_limit, end_limit = "12:00", "17:00"
            elif "morning" in tod:
                time_slot_label = "Morning (08:00 AM – 12:00 PM)"
                start_limit, end_limit = "08:00", "12:00"
            elif "evening" in tod:
                time_slot_label = "Evening (17:00 PM – 21:00 PM)"
                start_limit, end_limit = "17:00", "21:00"
            else:
                start_limit, end_limit = "00:00", "23:59"

            for e in combined_events:
                e_start = e.get("start_time", "00:00")
                if not (e_start >= end_limit or e.get("end_time", "23:59") <= start_limit):
                    filtered_events.append(e)
        else:
            filtered_events = combined_events

        # Free / Busy Availability Analysis
        availability = {
            "is_free": len(filtered_events) == 0,
            "conflicting_count": len(filtered_events),
            "time_slot": time_slot_label or (f"All Day on {target_date}" if target_date else "Retrieved Period"),
            "conflicts": [f"{e['title']} ({e['start_time']} - {e['end_time']})" for e in filtered_events]
        }

        return {
            "tool": "get_schedule",
            "query": query,
            "target_date": target_date,
            "time_of_day": time_of_day,
            "total_found": len(filtered_events),
            "events": filtered_events,
            "availability": availability,
            "rag_chunks": [r.get("_doc_snippet", "") for r in rag_results if r.get("_doc_snippet")]
        }

    # --------------------------------------------------------------------------
    # TOOL 2: update_schedule
    # --------------------------------------------------------------------------
    def update_schedule(
        self,
        action: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Tool 2: Adds, updates, or removes schedule entries.
        Automatically syncs vector database embeddings.
        """
        action = action.lower().strip()

        # 1. ADD ACTION
        if action in ["add", "create", "insert"]:
            title = event_data.get("title", "New Meeting")
            date_val = event_data.get("date", self.base_date.strftime("%Y-%m-%d"))
            start_time = event_data.get("start_time", "09:00")
            end_time = event_data.get("end_time")

            if not end_time:
                # Default 1 hour duration
                try:
                    s_dt = datetime.strptime(start_time, "%H:%M")
                    end_time = (s_dt + timedelta(hours=1)).strftime("%H:%M")
                except Exception:
                    end_time = "10:00"

            # Check for conflict
            existing_on_date = [
                e for e in self.vector_store.list_all_events()
                if e.get("date") == date_val
            ]
            conflicts = []
            for e in existing_on_date:
                e_start = e.get("start_time", "00:00")
                e_end = e.get("end_time", "23:59")
                # Overlap check
                if not (end_time <= e_start or start_time >= e_end):
                    conflicts.append(e)

            new_event = {
                "title": title,
                "category": event_data.get("category", "meeting"),
                "date": date_val,
                "start_time": start_time,
                "end_time": end_time,
                "location": event_data.get("location", "Room / Online"),
                "participants": event_data.get("participants", ["You"]),
                "description": event_data.get("description", f"Scheduled: {title}"),
                "status": "confirmed"
            }

            created = self.vector_store.add_event(new_event)
            return {
                "tool": "update_schedule",
                "action": "add",
                "success": True,
                "event": created,
                "conflicts_detected": [c["title"] for c in conflicts],
                "message": (
                    f"Successfully added '{title}' on {date_val} from {start_time} to {end_time}."
                    + (f" ⚠️ Note: overlaps with {', '.join(c['title'] for c in conflicts)}." if conflicts else "")
                )
            }

        # 2. UPDATE / MOVE ACTION
        elif action in ["update", "move", "reschedule", "modify", "edit"]:
            target_id = event_data.get("id")
            target_event = None

            # If no ID specified, locate via semantic search or target attributes
            if not target_id:
                lookup_query = event_data.get("search_query") or event_data.get("title", "")
                old_time = event_data.get("old_start_time")
                
                # Check all events
                all_evts = self.vector_store.list_all_events()
                
                # If old_time is specified (e.g., "move my meeting from 2 PM to 4 PM")
                if old_time:
                    matched = [e for e in all_evts if e.get("start_time") == old_time]
                    if matched:
                        # Prioritize today/tomorrow or closest to base_date
                        target_event = matched[0]

                if not target_event and lookup_query:
                    rag_matches = self.vector_store.query_rag(lookup_query, n_results=3)
                    if rag_matches:
                        target_event = rag_matches[0]

            else:
                target_event = self.vector_store.get_event(target_id)

            if not target_event:
                return {
                    "tool": "update_schedule",
                    "action": "update",
                    "success": False,
                    "message": "Could not identify which event to update. Please specify the title, date, or time."
                }

            # Calculate updated fields
            updated_payload = dict(target_event)
            if "date" in event_data and event_data["date"]:
                updated_payload["date"] = event_data["date"]
            if "title" in event_data and event_data["title"]:
                updated_payload["title"] = event_data["title"]
            if "new_start_time" in event_data and event_data["new_start_time"]:
                new_start = event_data["new_start_time"]
                # Adjust end time keeping original duration
                try:
                    orig_s = datetime.strptime(target_event["start_time"], "%H:%M")
                    orig_e = datetime.strptime(target_event["end_time"], "%H:%M")
                    duration = orig_e - orig_s
                    new_s_dt = datetime.strptime(new_start, "%H:%M")
                    new_e_dt = new_s_dt + duration
                    updated_payload["start_time"] = new_start
                    updated_payload["end_time"] = new_e_dt.strftime("%H:%M")
                except Exception:
                    updated_payload["start_time"] = new_start
            elif "start_time" in event_data:
                updated_payload["start_time"] = event_data["start_time"]
            if "end_time" in event_data and event_data["end_time"]:
                updated_payload["end_time"] = event_data["end_time"]

            res = self.vector_store.update_event(updated_payload)
            return {
                "tool": "update_schedule",
                "action": "update",
                "success": True,
                "previous_event": target_event,
                "updated_event": res,
                "message": f"Successfully moved '{res['title']}' to {res['date']} at {res['start_time']} - {res['end_time']}."
            }

        # 3. REMOVE / CANCEL ACTION
        elif action in ["remove", "delete", "cancel"]:
            target_id = event_data.get("id")
            target_event = None

            if not target_id:
                lookup_query = event_data.get("title") or event_data.get("search_query", "")
                if lookup_query:
                    rag_matches = self.vector_store.query_rag(lookup_query, n_results=1)
                    if rag_matches:
                        target_event = rag_matches[0]
                        target_id = target_event["id"]
            else:
                target_event = self.vector_store.get_event(target_id)

            if not target_id or not target_event:
                return {
                    "tool": "update_schedule",
                    "action": "remove",
                    "success": False,
                    "message": "Could not find matching event to remove."
                }

            deleted = self.vector_store.delete_event(target_id)
            return {
                "tool": "update_schedule",
                "action": "remove",
                "success": deleted,
                "removed_event": target_event,
                "message": f"Successfully removed event '{target_event['title']}' from your schedule."
            }

        return {
            "tool": "update_schedule",
            "action": action,
            "success": False,
            "message": f"Unknown action: {action}"
        }

    # --------------------------------------------------------------------------
    # AUTONOMOUS AGENT REASONING ENGINE
    # --------------------------------------------------------------------------
    def process_request(self, user_prompt: str, reference_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Agentic reasoning cycle:
        1. Analyzes user intent & temporal references.
        2. Decides whether to retrieve information or execute a tool.
        3. Invokes get_schedule or update_schedule with structured parameters.
        4. Inspects RAG vector results and tool outputs.
        5. Synthesizes a natural, helpful, formatted response with execution trace.
        """
        if reference_date:
            try:
                self.base_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
            except Exception:
                pass

        p = user_prompt.strip().lower()

        # Step 1: Detect action verbs (add, move, reschedule, delete) vs read (what, am I free, show, list)
        is_add = bool(re.search(r"\b(add|create|schedule|book|new\s+meeting|new\s+task|new\s+appointment)\b", p))
        is_move = bool(re.search(r"\b(move|reschedule|shift|change|delay|push)\b", p))
        is_remove = bool(re.search(r"\b(remove|delete|cancel|clear|drop)\b", p))

        # Check for specific temporal identifiers
        parsed_date = parse_relative_date(p, self.base_date)
        time_of_day = None
        if "afternoon" in p:
            time_of_day = "afternoon"
        elif "morning" in p:
            time_of_day = "morning"
        elif "evening" in p:
            time_of_day = "evening"

        trace = {
            "user_prompt": user_prompt,
            "reference_date": self.base_date.strftime("%Y-%m-%d (%A)"),
            "thought": "",
            "tool_called": None,
            "tool_arguments": None,
            "tool_result": None,
            "rag_context": [],
            "decision": ""
        }

        # ----------------------------------------------------------------------
        # CASE 1: MOVE / RESCHEDULE
        # Example: "Move my meeting from 2 PM to 4 PM."
        # ----------------------------------------------------------------------
        if is_move:
            trace["thought"] = "User wants to reschedule an existing event. I need to identify the target event and execute update_schedule."
            trace["decision"] = "Call update_schedule(action='update')"
            
            # Extract times: from X to Y
            time_from_match = re.search(r"from\s+([0-9:apm\s]+)\s+to\s+([0-9:apm\s]+)", p)
            old_time = None
            new_time = None
            if time_from_match:
                old_time = parse_time_str(time_from_match.group(1))
                new_time = parse_time_str(time_from_match.group(2))
            else:
                times_found = re.findall(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", p)
                if len(times_found) >= 2:
                    old_time = parse_time_str(times_found[0])
                    new_time = parse_time_str(times_found[1])
                elif len(times_found) == 1:
                    new_time = parse_time_str(times_found[0])

            event_payload = {
                "search_query": p,
                "old_start_time": old_time,
                "new_start_time": new_time,
                "date": parsed_date.strftime("%Y-%m-%d") if parsed_date else None
            }

            trace["tool_called"] = "update_schedule"
            trace["tool_arguments"] = {"action": "update", "event_data": event_payload}

            tool_res = self.update_schedule("update", event_payload)
            trace["tool_result"] = tool_res

            if tool_res["success"]:
                upd = tool_res["updated_event"]
                prev = tool_res["previous_event"]
                reply = (
                    f"✅ **Event Rescheduled Successfully!**\n\n"
                    f"• **Event:** {upd['title']}\n"
                    f"• **Previous Time:** {prev.get('date', '')} at {prev.get('start_time', '')} - {prev.get('end_time', '')}\n"
                    f"• **New Time:** {upd.get('date', '')} at {upd.get('start_time', '')} - {upd.get('end_time', '')}\n"
                    f"• **Location:** {upd.get('location', 'N/A')}\n\n"
                    f"Your calendar and vector database have been updated."
                )
            else:
                reply = f"⚠️ I encountered an issue updating your schedule: {tool_res['message']}"

            return {"reply": reply, "trace": trace, "events_updated": tool_res["success"]}

        # ----------------------------------------------------------------------
        # CASE 2: ADD EVENT
        # Example: "Add a meeting on August 15 at 3 PM."
        # ----------------------------------------------------------------------
        elif is_add:
            trace["thought"] = "User requests adding a new schedule item. I will parse date, time, title, and call update_schedule(action='add')."
            trace["decision"] = "Call update_schedule(action='add')"

            start_time = parse_time_str(p) or "09:00"
            target_date_str = parsed_date.strftime("%Y-%m-%d") if parsed_date else self.base_date.strftime("%Y-%m-%d")

            # Determine category
            category = "meeting"
            if "workshop" in p:
                category = "workshop"
            elif "task" in p:
                category = "task"
            elif "appointment" in p or "doctor" in p or "dentist" in p:
                category = "appointment"

            # Extract title if possible
            title = "New Meeting"
            # Strip common prefixes
            title_clean = re.sub(r"^(please\s+)?(add|schedule|create|book)\s+(a|an)?\s*", "", user_prompt, flags=re.IGNORECASE)
            title_clean = re.sub(r"\s+on\s+.*$", "", title_clean, flags=re.IGNORECASE)
            title_clean = re.sub(r"\s+at\s+.*$", "", title_clean, flags=re.IGNORECASE)
            title_clean = title_clean.strip()
            if len(title_clean) > 2:
                title = title_clean.capitalize()
            else:
                title = f"{category.capitalize()} Session"

            event_payload = {
                "title": title,
                "category": category,
                "date": target_date_str,
                "start_time": start_time,
                "location": "Online / Conference Room",
                "description": f"{title} scheduled via AI Assistant"
            }

            trace["tool_called"] = "update_schedule"
            trace["tool_arguments"] = {"action": "add", "event_data": event_payload}

            tool_res = self.update_schedule("add", event_payload)
            trace["tool_result"] = tool_res

            ev = tool_res["event"]
            conflicts_msg = ""
            if tool_res.get("conflicts_detected"):
                conflicts_msg = f"\n\n⚠️ **Notice:** This overlaps with an existing event: *{', '.join(tool_res['conflicts_detected'])}*."

            reply = (
                f"🗓️ **New Event Added!**\n\n"
                f"• **Title:** {ev['title']}\n"
                f"• **Category:** {ev['category'].upper()}\n"
                f"• **Date:** {ev['date']} ({ev.get('day_of_week', '')})\n"
                f"• **Time:** {ev['start_time']} - {ev['end_time']}\n"
                f"• **Location:** {ev['location']}{conflicts_msg}\n\n"
                f"The event has been indexed into ChromaDB."
            )

            return {"reply": reply, "trace": trace, "events_updated": True}

        # ----------------------------------------------------------------------
        # CASE 3: REMOVE / CANCEL
        # ----------------------------------------------------------------------
        elif is_remove:
            trace["thought"] = "User requests removing/cancelling an event. Calling update_schedule(action='remove')."
            trace["decision"] = "Call update_schedule(action='remove')"

            event_payload = {"title": user_prompt, "search_query": user_prompt}
            trace["tool_called"] = "update_schedule"
            trace["tool_arguments"] = {"action": "remove", "event_data": event_payload}

            tool_res = self.update_schedule("remove", event_payload)
            trace["tool_result"] = tool_res

            if tool_res["success"]:
                rem = tool_res["removed_event"]
                reply = (
                    f"🗑️ **Event Cancelled**\n\n"
                    f"Successfully removed **{rem['title']}** scheduled on {rem['date']} from your calendar and vector store."
                )
            else:
                reply = f"⚠️ Could not cancel the event: {tool_res['message']}"

            return {"reply": reply, "trace": trace, "events_updated": tool_res["success"]}

        # ----------------------------------------------------------------------
        # CASE 4: INFORMATIONAL RETRIEVAL (get_schedule)
        # Examples:
        # - “What do I have scheduled tomorrow?”
        # - “Am I free Friday afternoon?”
        # - "Show me all workshops"
        # ----------------------------------------------------------------------
        else:
            trace["thought"] = "User is querying their schedule. Deciding to invoke get_schedule to retrieve details from ChromaDB vector store."
            trace["decision"] = "Call get_schedule()"

            target_date_str = parsed_date.strftime("%Y-%m-%d") if parsed_date else None
            
            # Detect category filter
            category = None
            if "workshop" in p:
                category = "workshop"
            elif "task" in p:
                category = "task"
            elif "appointment" in p or "doctor" in p or "dentist" in p:
                category = "appointment"
            elif "meeting" in p:
                category = "meeting"

            tool_args = {
                "query": user_prompt,
                "target_date": target_date_str,
                "time_of_day": time_of_day,
                "category": category,
                "n_results": 5
            }
            trace["tool_called"] = "get_schedule"
            trace["tool_arguments"] = tool_args

            tool_res = self.get_schedule(**tool_args)
            trace["tool_result"] = tool_res
            trace["rag_context"] = tool_res.get("rag_chunks", [])

            # Synthesize answer
            events = tool_res["events"]
            avail = tool_res["availability"]

            # Specific check for "Am I free..." questions
            is_free_query = "free" in p or "available" in p or "any openings" in p

            if is_free_query:
                time_target_desc = f"{parsed_date.strftime('%A, %b %d') if parsed_date else 'that time'}"
                if time_of_day:
                    time_target_desc += f" in the {time_of_day}"

                if avail["is_free"]:
                    reply = (
                        f"🟢 **Yes, you are completely free!**\n\n"
                        f"You have **no events scheduled** for **{time_target_desc}**.\n"
                        f"Your calendar is wide open for focused work or booking new meetings."
                    )
                else:
                    conflicts_list = "\n".join([f"• **{e['title']}**: {e['start_time']} – {e['end_time']} ({e['category']})" for e in events])
                    reply = (
                        f"🟡 **You have commitments during this period:**\n\n"
                        f"For **{time_target_desc}**, you have the following {len(events)} event(s):\n\n"
                        f"{conflicts_list}\n\n"
                        f"Outside of these hours, your calendar is open."
                    )
            else:
                # General schedule overview (e.g., "What do I have scheduled tomorrow?")
                date_heading = parsed_date.strftime('%A, %B %d, %Y') if parsed_date else "Upcoming Schedule"
                if not events:
                    reply = (
                        f"📅 **Schedule for {date_heading}:**\n\n"
                        f"You have no events scheduled. You are completely free!"
                    )
                else:
                    lines = [f"📅 **Schedule for {date_heading}:**\n"]
                    for e in events:
                        cat_emoji = {
                            "meeting": "💼",
                            "workshop": "🛠️",
                            "task": "📝",
                            "appointment": "🩺"
                        }.get(e.get("category", ""), "📌")
                        lines.append(
                            f"• {cat_emoji} **{e['title']}**\n"
                            f"   ⏰ {e['start_time']} – {e['end_time']} | 📍 {e.get('location', 'Online')}\n"
                            f"   ℹ️ {e.get('description', '')}"
                        )
                    reply = "\n\n".join(lines)

            return {"reply": reply, "trace": trace, "events_updated": False}
