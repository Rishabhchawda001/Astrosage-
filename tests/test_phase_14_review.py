"""Phase 14 — Human Review Queue Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestReview:
    def test_imports(self):
        from core.review.engine import ReviewEngine, ReviewItem, ReviewPriority
        assert ReviewEngine is not None

    def test_queue_item(self):
        from core.review.engine import ReviewEngine, ReviewReason, ReviewPriority
        engine = ReviewEngine()
        item = engine.queue("KU-001", ReviewReason.LOW_CONFIDENCE, ReviewPriority.HIGH,
                            title="Low confidence item")
        assert item.item_id is not None
        assert item.knowledge_uuid == "KU-001"

    def test_queue_low_confidence(self):
        from core.review.engine import ReviewEngine
        engine = ReviewEngine()
        item = engine.queue_low_confidence("KU-002", confidence=0.2)
        assert item.priority.value == "high"
        assert item.confidence == 0.2

    def test_queue_conflict(self):
        from core.review.engine import ReviewEngine
        engine = ReviewEngine()
        item = engine.queue_conflict("KU-003", conflict_count=5)
        assert item.priority.value == "critical"

    def test_queue_single_source(self):
        from core.review.engine import ReviewEngine
        engine = ReviewEngine()
        item = engine.queue_single_source("KU-004", source_id="SRC-001")
        assert "SRC-001" in item.source_ids

    def test_approve(self):
        from core.review.engine import ReviewEngine, ReviewReason, ReviewStatus
        engine = ReviewEngine()
        item = engine.queue("KU-005", ReviewReason.MANUAL_INSPECTION)
        result = engine.approve(item.item_id, reviewer_notes="Verified by expert")
        assert result is True
        assert engine._items[item.item_id].status == ReviewStatus.APPROVED

    def test_reject(self):
        from core.review.engine import ReviewEngine, ReviewReason, ReviewStatus
        engine = ReviewEngine()
        item = engine.queue("KU-006", ReviewReason.BROKEN_HIERARCHY)
        result = engine.reject(item.item_id, reviewer_notes="Irrelevant")
        assert result is True
        assert engine._items[item.item_id].status == ReviewStatus.REJECTED

    def test_get_pending(self):
        from core.review.engine import ReviewEngine, ReviewReason
        engine = ReviewEngine()
        i1 = engine.queue("KU-010", ReviewReason.LOW_CONFIDENCE)
        i2 = engine.queue("KU-011", ReviewReason.CONFLICT)
        engine.approve(i1.item_id)
        pending = engine.get_pending()
        assert len(pending) == 1

    def test_get_by_priority(self):
        from core.review.engine import ReviewEngine, ReviewReason, ReviewPriority
        engine = ReviewEngine()
        engine.queue("KU-020", ReviewReason.LOW_CONFIDENCE, ReviewPriority.HIGH)
        engine.queue("KU-021", ReviewReason.CONFLICT, ReviewPriority.CRITICAL)
        critical = engine.get_by_priority(ReviewPriority.CRITICAL)
        assert len(critical) == 1

    def test_get_by_knowledge(self):
        from core.review.engine import ReviewEngine, ReviewReason
        engine = ReviewEngine()
        engine.queue("KU-030", ReviewReason.LOW_CONFIDENCE)
        engine.queue("KU-030", ReviewReason.CONFLICT)
        items = engine.get_by_knowledge("KU-030")
        assert len(items) == 2

    def test_summary(self):
        from core.review.engine import ReviewEngine, ReviewReason, ReviewPriority
        engine = ReviewEngine()
        engine.queue("KU-040", ReviewReason.LOW_CONFIDENCE, ReviewPriority.HIGH)
        engine.queue("KU-041", ReviewReason.CONFLICT, ReviewPriority.CRITICAL)
        s = engine.summary()
        assert s["total"] == 2
        assert "by_priority" in s
        assert "by_reason" in s
        assert "by_status" in s

    def test_count(self):
        from core.review.engine import ReviewEngine, ReviewReason
        engine = ReviewEngine()
        assert engine.count() == 0
        engine.queue("KU-050", ReviewReason.CITATION_MISSING)
        assert engine.count() == 1
