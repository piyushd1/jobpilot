"""Embedding generation pipeline for resumes and job descriptions.

Generates embeddings for candidate profiles and job descriptions,
stores them in Qdrant, and supports idempotent re-runs via content hashing.
"""

from __future__ import annotations

import hashlib

from src.models.schemas import CandidateProfile, JobDescription
from src.services.llm_gateway import llm_gateway
from src.services.vector_store import (
    CANDIDATE_PROFILES_COLLECTION,
    JOB_DESCRIPTIONS_COLLECTION,
    vector_store,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingPipeline:
    """Generate and store embeddings for candidate profiles and job descriptions."""

    @staticmethod
    def _content_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_profile_text(profile: CandidateProfile) -> str:
        parts = []
        if profile.summary:
            parts.append(profile.summary)
        if profile.target_roles:
            parts.append(f"Target roles: {', '.join(profile.target_roles)}")
        for exp in profile.work_experience:
            exp_text = f"{exp.title} at {exp.company}"
            if exp.description:
                exp_text += f": {exp.description}"
            parts.append(exp_text)
        if profile.skills:
            parts.append(f"Skills: {', '.join(profile.skills)}")
        return "\n".join(parts)

    @staticmethod
    def _build_skills_text(profile: CandidateProfile) -> str:
        all_skills = list(profile.skills)
        for exp in profile.work_experience:
            all_skills.extend(exp.skills_used)
        return ", ".join(dict.fromkeys(all_skills))

    @staticmethod
    def _build_job_text(job: JobDescription) -> str:
        parts = [f"{job.title} at {job.company}"]
        if job.location:
            parts.append(f"Location: {job.location}")
        if job.description:
            parts.append(job.description)
        if job.required_skills:
            parts.append(f"Required: {', '.join(job.required_skills)}")
        if job.preferred_skills:
            parts.append(f"Preferred: {', '.join(job.preferred_skills)}")
        return "\n".join(parts)

    async def generate_candidate_embeddings(
        self, user_id: str, resume_id: str, profile: CandidateProfile,
    ) -> dict[str, str]:
        embedding_ids: dict[str, str] = {}

        profile_text = self._build_profile_text(profile)
        profile_point_id = f"{resume_id}_full_profile"
        profile_embs = await llm_gateway.embed([profile_text])
        await vector_store.upsert(
            collection=CANDIDATE_PROFILES_COLLECTION,
            point_id=profile_point_id,
            vector=profile_embs[0],
            payload={"user_id": user_id, "resume_id": resume_id,
                     "embedding_type": "full_profile",
                     "content_hash": self._content_hash(profile_text)},
        )
        embedding_ids["emb_full_profile"] = profile_point_id

        skills_text = self._build_skills_text(profile)
        if skills_text:
            skills_point_id = f"{resume_id}_skills"
            skills_embs = await llm_gateway.embed([skills_text])
            await vector_store.upsert(
                collection=CANDIDATE_PROFILES_COLLECTION,
                point_id=skills_point_id,
                vector=skills_embs[0],
                payload={"user_id": user_id, "resume_id": resume_id,
                         "embedding_type": "skills",
                         "content_hash": self._content_hash(skills_text)},
            )
            embedding_ids["emb_skills"] = skills_point_id

        for i, exp in enumerate(profile.work_experience):
            exp_text = f"{exp.title} at {exp.company}"
            if exp.description:
                exp_text += f": {exp.description}"
            exp_point_id = f"{resume_id}_exp_{i}"
            exp_embs = await llm_gateway.embed([exp_text])
            await vector_store.upsert(
                collection=CANDIDATE_PROFILES_COLLECTION,
                point_id=exp_point_id,
                vector=exp_embs[0],
                payload={"user_id": user_id, "resume_id": resume_id,
                         "embedding_type": f"experience_{i}",
                         "content_hash": self._content_hash(exp_text)},
            )
            embedding_ids[f"emb_exp_{i}"] = exp_point_id

        return embedding_ids

    async def generate_job_embedding(self, campaign_id: str, job: JobDescription) -> str:
        job_text = self._build_job_text(job)
        content_hash = self._content_hash(job_text)
        point_id = f"{campaign_id}_{content_hash[:16]}"
        embeddings = await llm_gateway.embed([job_text])
        await vector_store.upsert(
            collection=JOB_DESCRIPTIONS_COLLECTION,
            point_id=point_id,
            vector=embeddings[0],
            payload={"campaign_id": campaign_id, "title": job.title,
                     "company": job.company, "content_hash": content_hash},
        )
        return point_id

    async def batch_generate_job_embeddings(
        self, campaign_id: str, jobs: list[JobDescription],
    ) -> list[str]:
        texts = [self._build_job_text(j) for j in jobs]
        hashes = [self._content_hash(t) for t in texts]
        all_embeddings = await llm_gateway.embed(texts)
        points = []
        point_ids = []
        for job, embedding, h in zip(jobs, all_embeddings, hashes):
            pid = f"{campaign_id}_{h[:16]}"
            point_ids.append(pid)
            points.append({"id": pid, "vector": embedding,
                           "payload": {"campaign_id": campaign_id,
                                       "title": job.title, "company": job.company,
                                       "content_hash": h}})
        if points:
            await vector_store.upsert_batch(JOB_DESCRIPTIONS_COLLECTION, points)
        return point_ids


embedding_pipeline = EmbeddingPipeline()
