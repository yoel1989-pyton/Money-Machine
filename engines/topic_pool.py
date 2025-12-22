#!/usr/bin/env python3
"""
MONEY MACHINE AI - TOPIC POOL ENGINE
=====================================
Self-rotating, performance-based topic selection.
No code changes required - edit topics.json instead.

Features:
- Automatic topic rotation
- Performance-based promotion/demotion
- Cooldown to prevent repetition
- Experimental topic injection
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple


class TopicPool:
    """
    Self-managing topic selection system.
    Reads from topics.json, tracks performance, auto-promotes/demotes.
    """
    
    def __init__(self, topics_file: str = None):
        if topics_file is None:
            self.topics_file = Path(__file__).parent.parent / "data" / "topics.json"
        else:
            self.topics_file = Path(topics_file)
        
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load topics from JSON file."""
        if not self.topics_file.exists():
            raise FileNotFoundError(f"Topics file not found: {self.topics_file}")
        
        with open(self.topics_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save(self):
        """Save topics back to JSON file."""
        self.data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        with open(self.topics_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def get_next_topic(self) -> Tuple[str, str]:
        """
        Get the next topic to use.
        
        Returns:
            Tuple of (topic, pool_name)
        
        Selection logic:
        1. Check if we should inject an experimental topic (15% chance)
        2. Prefer high_performing topics (if any)
        3. Fall back to core topics
        4. Avoid recently used topics (cooldown)
        """
        settings = self.data.get("settings", {})
        pools = self.data.get("pools", {})
        history = self.data.get("usage_history", [])
        
        # Get cooldown window
        cooldown_hours = settings.get("cooldown_hours", 72)
        cooldown_cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
        
        # Get recently used topics
        recent_topics = set()
        for entry in history:
            try:
                used_at = datetime.fromisoformat(entry["used_at"].replace("Z", "+00:00"))
                if used_at > cooldown_cutoff:
                    recent_topics.add(entry["topic"])
            except:
                pass
        
        # Decide: experimental injection?
        injection_rate = settings.get("experimental_injection_rate", 0.15)
        inject_experimental = random.random() < injection_rate
        
        selected_topic = None
        selected_pool = None
        
        # Try experimental first if injection triggered
        if inject_experimental:
            experimental = pools.get("experimental", [])
            available = [t for t in experimental if t not in recent_topics]
            if available:
                selected_topic = random.choice(available)
                selected_pool = "experimental"
        
        # Try high_performing
        if not selected_topic:
            high_perf = pools.get("high_performing", [])
            available = [t for t in high_perf if t not in recent_topics]
            if available:
                selected_topic = random.choice(available)
                selected_pool = "high_performing"
        
        # Fall back to core
        if not selected_topic:
            core = pools.get("core", [])
            available = [t for t in core if t not in recent_topics]
            if available:
                selected_topic = random.choice(available)
                selected_pool = "core"
        
        # Last resort: any topic from any pool
        if not selected_topic:
            all_topics = (
                pools.get("core", []) +
                pools.get("high_performing", []) +
                pools.get("experimental", [])
            )
            if all_topics:
                selected_topic = random.choice(all_topics)
                selected_pool = "fallback"
        
        if not selected_topic:
            raise ValueError("No topics available in any pool")
        
        # Record usage
        self._record_usage(selected_topic, selected_pool)
        
        return selected_topic, selected_pool
    
    def _record_usage(self, topic: str, pool: str):
        """Record that a topic was used."""
        if "usage_history" not in self.data:
            self.data["usage_history"] = []
        
        self.data["usage_history"].append({
            "topic": topic,
            "pool": pool,
            "used_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep only last 100 entries
        self.data["usage_history"] = self.data["usage_history"][-100:]
        
        self._save()
    
    def record_performance(self, topic: str, views_1hr: int, retention_pct: float = None):
        """
        Record performance data for a topic.
        Called after 1 hour to track how the video performed.
        """
        if "performance_log" not in self.data:
            self.data["performance_log"] = []
        
        self.data["performance_log"].append({
            "topic": topic,
            "views_1hr": views_1hr,
            "retention_pct": retention_pct,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep only last 200 entries
        self.data["performance_log"] = self.data["performance_log"][-200:]
        
        # Auto-promote/demote based on performance
        self._auto_adjust_pools(topic, views_1hr)
        
        self._save()
    
    def _auto_adjust_pools(self, topic: str, views_1hr: int):
        """
        Automatically move topics between pools based on performance.
        """
        settings = self.data.get("settings", {})
        pools = self.data.get("pools", {})
        
        promotion_threshold = settings.get("promotion_threshold_views_1hr", 500)
        demotion_threshold = settings.get("demotion_threshold_views_1hr", 50)
        
        # Find which pool the topic is in
        current_pool = None
        for pool_name, topics in pools.items():
            if topic in topics:
                current_pool = pool_name
                break
        
        if not current_pool:
            return
        
        # Promotion logic
        if views_1hr >= promotion_threshold:
            if current_pool in ["core", "experimental"]:
                # Move to high_performing
                pools[current_pool].remove(topic)
                if "high_performing" not in pools:
                    pools["high_performing"] = []
                if topic not in pools["high_performing"]:
                    pools["high_performing"].append(topic)
                print(f"[TOPIC POOL] 📈 Promoted '{topic[:40]}...' to high_performing")
        
        # Demotion logic
        elif views_1hr <= demotion_threshold:
            if current_pool in ["core", "high_performing"]:
                # Move to cooldown
                pools[current_pool].remove(topic)
                if "cooldown" not in pools:
                    pools["cooldown"] = []
                if topic not in pools["cooldown"]:
                    pools["cooldown"].append(topic)
                print(f"[TOPIC POOL] 📉 Demoted '{topic[:40]}...' to cooldown")
    
    def restore_from_cooldown(self):
        """
        Move topics from cooldown back to core after cooldown period.
        Call this periodically (e.g., daily).
        """
        settings = self.data.get("settings", {})
        pools = self.data.get("pools", {})
        cooldown_hours = settings.get("cooldown_hours", 72)
        
        # Check usage history to find when each cooldown topic was last used
        cooldown = pools.get("cooldown", [])
        if not cooldown:
            return
        
        history = self.data.get("usage_history", [])
        now = datetime.now(timezone.utc)
        
        to_restore = []
        for topic in cooldown:
            # Find last usage
            last_used = None
            for entry in reversed(history):
                if entry["topic"] == topic:
                    try:
                        last_used = datetime.fromisoformat(
                            entry["used_at"].replace("Z", "+00:00")
                        )
                        break
                    except:
                        pass
            
            # If never used or cooldown expired, restore
            if last_used is None or (now - last_used).total_seconds() > cooldown_hours * 3600:
                to_restore.append(topic)
        
        # Move restored topics back to core
        for topic in to_restore:
            pools["cooldown"].remove(topic)
            pools["core"].append(topic)
            print(f"[TOPIC POOL] ♻️ Restored '{topic[:40]}...' from cooldown to core")
        
        if to_restore:
            self._save()
    
    def add_topic(self, topic: str, pool: str = "experimental"):
        """Add a new topic to a pool."""
        pools = self.data.get("pools", {})
        
        if pool not in pools:
            pools[pool] = []
        
        if topic not in pools[pool]:
            pools[pool].append(topic)
            self._save()
            print(f"[TOPIC POOL] ➕ Added '{topic[:40]}...' to {pool}")
    
    def remove_topic(self, topic: str):
        """Remove a topic from all pools."""
        pools = self.data.get("pools", {})
        
        for pool_name, topics in pools.items():
            if topic in topics:
                topics.remove(topic)
                print(f"[TOPIC POOL] ➖ Removed '{topic[:40]}...' from {pool_name}")
        
        self._save()
    
    def get_stats(self) -> dict:
        """Get pool statistics."""
        pools = self.data.get("pools", {})
        history = self.data.get("usage_history", [])
        perf = self.data.get("performance_log", [])
        
        return {
            "core_count": len(pools.get("core", [])),
            "high_performing_count": len(pools.get("high_performing", [])),
            "experimental_count": len(pools.get("experimental", [])),
            "cooldown_count": len(pools.get("cooldown", [])),
            "total_uses": len(history),
            "total_performance_records": len(perf),
            "last_updated": self.data.get("last_updated")
        }


# ============================================================
# CLI for manual management
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Topic Pool Manager")
    parser.add_argument("--stats", action="store_true", help="Show pool statistics")
    parser.add_argument("--next", action="store_true", help="Get next topic")
    parser.add_argument("--add", type=str, help="Add a topic to experimental pool")
    parser.add_argument("--restore", action="store_true", help="Restore cooldown topics")
    args = parser.parse_args()
    
    pool = TopicPool()
    
    if args.stats:
        stats = pool.get_stats()
        print("\n📊 Topic Pool Statistics:")
        print(f"   Core: {stats['core_count']} topics")
        print(f"   High Performing: {stats['high_performing_count']} topics")
        print(f"   Experimental: {stats['experimental_count']} topics")
        print(f"   Cooldown: {stats['cooldown_count']} topics")
        print(f"   Total uses: {stats['total_uses']}")
        print(f"   Last updated: {stats['last_updated']}")
    
    elif args.next:
        topic, pool_name = pool.get_next_topic()
        print(f"\n🎯 Next Topic: {topic}")
        print(f"   Pool: {pool_name}")
    
    elif args.add:
        pool.add_topic(args.add, "experimental")
    
    elif args.restore:
        pool.restore_from_cooldown()
        print("✅ Cooldown restoration complete")
    
    else:
        parser.print_help()
