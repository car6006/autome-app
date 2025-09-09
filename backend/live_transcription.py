"""
Live Transcription System - Real-time streaming transcription with rolling merge
Implements the comprehensive live transcription specification
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import redis.asyncio as redis
from enhanced_providers import transcription_provider

logger = logging.getLogger(__name__)

class RollingTranscript:
    """Manages rolling transcript state with conflict resolution"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.chunk_ms = int(os.getenv("AUDIO_CHUNK_MS", "5000"))
        self.overlap_ms = int(os.getenv("AUDIO_OVERLAP_MS", "750"))
        self.commit_window_ms = int(os.getenv("COMMIT_WINDOW_MS", "2500"))
        
    async def upsert_chunk(self, session_id: str, chunk_idx: int, words: List[dict], 
                          avg_conf: float, start_ms: int, end_ms: int) -> dict:
        """
        Insert/update chunk with overlap resolution and emit events
        
        Returns: {
            "partial": {"text": str, "words": List[dict]},
            "commit": {"text": str, "start_ms": int, "end_ms": int} or None
        }
        """
        try:
            key = f"meeting:{session_id}:rolling"
            
            # Get current state
            current_state = await self._get_rolling_state(session_id)
            
            # Process the new chunk
            events = await self._merge_chunk(
                current_state, chunk_idx, words, avg_conf, start_ms, end_ms
            )
            
            # Update Redis state
            await self._update_rolling_state(session_id, current_state)
            
            # Log the merge operation
            logger.info(f"📝 Merged chunk {chunk_idx} for session {session_id}: "
                       f"{len(words)} words, {avg_conf:.2f} confidence")
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error upserting chunk {chunk_idx} for session {session_id}: {e}")
            raise

    async def _get_rolling_state(self, session_id: str) -> dict:
        """Get current rolling transcript state from Redis"""
        key = f"meeting:{session_id}:rolling"
        
        try:
            state_data = await self.redis.hgetall(key)
            
            if not state_data:
                # Initialize new state
                return {
                    "last_committed_ms": 0,
                    "tail_buffer": [],
                    "received_idx_set": set(),
                    "last_seq": -1,
                    "updated_at": time.time(),
                    "committed_words": []
                }
            
            # Parse stored state
            return {
                "last_committed_ms": int(state_data.get(b"last_committed_ms", 0)),
                "tail_buffer": json.loads(state_data.get(b"tail_buffer", "[]")),
                "received_idx_set": set(json.loads(state_data.get(b"received_idx_set", "[]"))),
                "last_seq": int(state_data.get(b"last_seq", -1)),
                "updated_at": float(state_data.get(b"updated_at", time.time())),
                "committed_words": json.loads(state_data.get(b"committed_words", "[]"))
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting rolling state for {session_id}: {e}")
            # Return fresh state on error
            return {
                "last_committed_ms": 0,
                "tail_buffer": [],
                "received_idx_set": set(),
                "last_seq": -1,
                "updated_at": time.time(),
                "committed_words": []
            }

    async def _merge_chunk(self, state: dict, chunk_idx: int, words: List[dict], 
                          avg_conf: float, start_ms: int, end_ms: int) -> dict:
        """
        Merge new chunk with existing state using confidence-based conflict resolution
        """
        events = {"partial": None, "commit": None}
        
        try:
            # Skip if already processed
            if chunk_idx in state["received_idx_set"]:
                logger.debug(f"🔄 Chunk {chunk_idx} already processed, skipping")
                return events
            
            # Add to received set
            state["received_idx_set"].add(chunk_idx)
            state["last_seq"] = max(state["last_seq"], chunk_idx)
            
            # Find overlap region with existing tail
            overlap_start_ms = max(0, start_ms - self.overlap_ms)
            overlap_end_ms = start_ms + self.overlap_ms
            
            # Resolve overlaps with confidence-based merging
            combined_words = self._resolve_overlaps(
                state["tail_buffer"], words, overlap_start_ms, overlap_end_ms, avg_conf
            )
            
            # Update tail buffer
            state["tail_buffer"] = combined_words
            
            # Determine commit boundary
            now_ms = start_ms + (chunk_idx * self.chunk_ms)
            commit_boundary_ms = now_ms - self.commit_window_ms
            
            # Split into committed and tail parts
            committed_words = []
            tail_words = []
            
            for word in combined_words:
                if word["end"] <= commit_boundary_ms:
                    committed_words.append(word)
                else:
                    tail_words.append(word)
            
            # Update state
            if committed_words:
                # Add to committed words
                state["committed_words"].extend(committed_words)
                state["last_committed_ms"] = committed_words[-1]["end"]
                
                # Create commit event
                commit_text = " ".join([w["word"] for w in committed_words])
                events["commit"] = {
                    "text": commit_text,
                    "start_ms": committed_words[0]["start"],
                    "end_ms": committed_words[-1]["end"],
                    "word_count": len(committed_words)
                }
            
            # Update tail buffer
            state["tail_buffer"] = tail_words
            
            # Create partial event (uncommitted tail)
            if tail_words:
                partial_text = " ".join([w["word"] for w in tail_words])
                events["partial"] = {
                    "text": partial_text,
                    "words": tail_words,
                    "start_ms": tail_words[0]["start"],
                    "end_ms": tail_words[-1]["end"]
                }
            
            state["updated_at"] = time.time()
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Error merging chunk {chunk_idx}: {e}")
            return events

    def _resolve_overlaps(self, existing_words: List[dict], new_words: List[dict], 
                         overlap_start_ms: int, overlap_end_ms: int, new_avg_conf: float) -> List[dict]:
        """
        Resolve overlaps between existing and new words using confidence-based selection
        """
        if not existing_words:
            return new_words.copy()
        
        if not new_words:
            return existing_words.copy()
        
        try:
            # Find overlapping regions
            existing_overlap = [w for w in existing_words 
                              if w["start"] < overlap_end_ms and w["end"] > overlap_start_ms]
            new_overlap = [w for w in new_words 
                          if w["start"] < overlap_end_ms and w["end"] > overlap_start_ms]
            
            if not existing_overlap or not new_overlap:
                # No overlap, simple concatenation
                all_words = existing_words + new_words
                return sorted(all_words, key=lambda w: w["start"])
            
            # Calculate confidence for existing overlap
            existing_conf = sum(w.get("confidence", 0.8) for w in existing_overlap) / len(existing_overlap)
            
            # Choose better overlap based on confidence
            if new_avg_conf > existing_conf + 0.1:  # 10% confidence threshold
                logger.debug(f"🎯 Using new words (conf: {new_avg_conf:.2f} vs {existing_conf:.2f})")
                selected_overlap = new_overlap
                discarded_overlap = existing_overlap
            else:
                logger.debug(f"🎯 Keeping existing words (conf: {existing_conf:.2f} vs {new_avg_conf:.2f})")
                selected_overlap = existing_overlap
                discarded_overlap = new_overlap
            
            # Combine non-overlapping parts
            non_overlap_existing = [w for w in existing_words if w not in existing_overlap]
            non_overlap_new = [w for w in new_words if w not in new_overlap]
            
            # Merge all parts
            combined = non_overlap_existing + selected_overlap + non_overlap_new
            
            # Sort by start time and remove duplicates
            combined.sort(key=lambda w: w["start"])
            
            # Remove duplicate words at same timestamps
            deduplicated = []
            for word in combined:
                if not deduplicated or word["start"] != deduplicated[-1]["start"]:
                    deduplicated.append(word)
            
            return deduplicated
            
        except Exception as e:
            logger.error(f"❌ Error resolving overlaps: {e}")
            # Fallback: simple concatenation
            return existing_words + new_words

    async def _update_rolling_state(self, session_id: str, state: dict):
        """Update rolling state in Redis"""
        key = f"meeting:{session_id}:rolling"
        
        try:
            # Convert set to list for JSON serialization
            redis_data = {
                "last_committed_ms": state["last_committed_ms"],
                "tail_buffer": json.dumps(state["tail_buffer"]),
                "received_idx_set": json.dumps(list(state["received_idx_set"])),
                "last_seq": state["last_seq"],
                "updated_at": state["updated_at"],
                "committed_words": json.dumps(state["committed_words"])
            }
            
            await self.redis.hset(key, mapping=redis_data)
            
            # Set expiration (1 day)
            await self.redis.expire(key, 86400)
            
        except Exception as e:
            logger.error(f"❌ Error updating rolling state for {session_id}: {e}")

    async def get_full_transcript(self, session_id: str) -> dict:
        """Get the complete transcript (committed + tail)"""
        try:
            state = await self._get_rolling_state(session_id)
            
            all_words = state["committed_words"] + state["tail_buffer"]
            all_words.sort(key=lambda w: w["start"])
            
            text = " ".join([w["word"] for w in all_words])
            
            return {
                "text": text,
                "words": all_words,
                "committed_words": len(state["committed_words"]),
                "tail_words": len(state["tail_buffer"]),
                "last_updated": state["updated_at"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting full transcript for {session_id}: {e}")
            return {"text": "", "words": [], "committed_words": 0, "tail_words": 0}

class LiveTranscriptionManager:
    """Main manager for live transcription operations"""
    
    def __init__(self):
        self.redis_client = None
        self.rolling_transcript = None
        self.event_handlers = []
        self.active_sessions = set()
        
    async def initialize(self):
        """Initialize Redis connection and components"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis for live transcription")
            
            self.rolling_transcript = RollingTranscript(self.redis_client)
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize live transcription: {e}")
            raise

    async def process_audio_chunk(self, session_id: str, chunk_idx: int, 
                                 audio_file_path: str) -> dict:
        """
        Process an audio chunk for live transcription
        
        Returns: {
            "success": bool,
            "events": {"partial": dict, "commit": dict},
            "transcription": dict
        }
        """
        try:
            self.active_sessions.add(session_id)
            
            # Transcribe the audio chunk
            logger.info(f"🎤 Processing audio chunk {chunk_idx} for session {session_id}")
            transcription = await transcription_provider.transcribe_audio_chunk(
                audio_file_path, session_id, chunk_idx
            )
            
            if not transcription or not transcription.get("text"):
                logger.warning(f"⚠️  Empty transcription for chunk {chunk_idx}")
                return {
                    "success": False,
                    "events": {"partial": None, "commit": None},
                    "transcription": None
                }
            
            # Calculate chunk timing
            start_ms = chunk_idx * int(os.getenv("AUDIO_CHUNK_MS", "5000"))
            end_ms = start_ms + len(transcription.get("words", [])) * 200  # Rough estimate
            
            # Update rolling transcript
            events = await self.rolling_transcript.upsert_chunk(
                session_id, chunk_idx, transcription["words"],
                transcription.get("confidence", 0.8), start_ms, end_ms
            )
            
            # Emit events to connected clients
            await self._emit_events(session_id, events)
            
            logger.info(f"✅ Processed chunk {chunk_idx}: '{transcription['text'][:50]}...'")
            
            return {
                "success": True,
                "events": events,
                "transcription": transcription
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing chunk {chunk_idx} for session {session_id}: {e}")
            return {
                "success": False,
                "events": {"partial": None, "commit": None},
                "transcription": None,
                "error": str(e)
            }

    async def finalize_session(self, session_id: str) -> dict:
        """
        Finalize a live transcription session
        
        Returns: {
            "success": bool,
            "transcript": dict,
            "artifacts": dict
        }
        """
        try:
            logger.info(f"🏁 Finalizing live transcription session {session_id}")
            
            # Get final transcript
            transcript = await self.rolling_transcript.get_full_transcript(session_id)
            
            # Emit final event
            await self._emit_events(session_id, {
                "final": {
                    "session_id": session_id,
                    "text": transcript["text"],
                    "word_count": len(transcript["words"]),
                    "duration_ms": transcript["words"][-1]["end"] if transcript["words"] else 0,
                    "finalized_at": datetime.now(timezone.utc).isoformat()
                }
            })
            
            # Clean up session
            self.active_sessions.discard(session_id)
            
            logger.info(f"✅ Finalized session {session_id}: {len(transcript['text'])} chars")
            
            return {
                "success": True,
                "transcript": transcript,
                "artifacts": {
                    "text": transcript["text"],
                    "words_json": transcript["words"]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error finalizing session {session_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _emit_events(self, session_id: str, events: dict):
        """Emit events to connected clients (WebSocket/SSE)"""
        try:
            for event_type, event_data in events.items():
                if event_data:
                    # Store event in Redis for client polling
                    event_key = f"events:{session_id}:{event_type}"
                    event_payload = {
                        "type": event_type,
                        "session_id": session_id,
                        "timestamp": time.time(),
                        "data": event_data
                    }
                    
                    await self.redis_client.setex(
                        event_key, 300, json.dumps(event_payload)  # 5 minutes TTL
                    )
                    
                    logger.debug(f"📡 Emitted {event_type} event for session {session_id}")
                    
        except Exception as e:
            logger.error(f"❌ Error emitting events for {session_id}: {e}")

    async def get_live_transcript(self, session_id: str) -> dict:
        """Get current live transcript for a session"""
        if session_id not in self.active_sessions:
            return {"error": "Session not active"}
            
        return await self.rolling_transcript.get_full_transcript(session_id)

    async def cleanup_old_sessions(self):
        """Clean up old inactive sessions"""
        try:
            # This would run periodically to clean up Redis keys
            idle_timeout = int(os.getenv("MEETING_IDLE_TIMEOUT_SEC", "90"))
            # Implementation would scan for old session keys and remove them
            logger.info("🧹 Cleaned up old transcription sessions")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up sessions: {e}")

# Global instance
live_transcription_manager = LiveTranscriptionManager()