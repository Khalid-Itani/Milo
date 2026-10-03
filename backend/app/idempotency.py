"""Durable request leases and atomic mutation results. No process-only locks."""
import hashlib
import json
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
from app.config import settings
from app.models import Mutation, utcnow
from app import services as svc

LEASE_SECONDS = 600

def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False).encode()).hexdigest()

def claim(factory, key, fingerprint):
    """Committed claim before the external call. Concurrent callers get 409."""
    token = str(uuid4())
    with factory() as s:
        with s.begin():
            svc.guard_owner(s)
            svc.profile(s, required=True)
            row = s.exec(svc.owned(Mutation).where(Mutation.key == key).with_for_update()).first()
            if row:
                if row.fingerprint != fingerprint:
                    raise HTTPException(409, "Idempotency-Key payload conflict")
                if row.state == "complete":
                    return row.id, None, row.result
                if svc.aware(row.lease_until) > utcnow():
                    raise HTTPException(409, "request_in_progress; retry with the same key")
                row.lease_token, row.lease_until = token, utcnow()+timedelta(seconds=LEASE_SECONDS)
            else:
                row = Mutation(id=str(uuid4()), owner_id=settings.demo_user_id, key=key,
                               fingerprint=fingerprint, lease_token=token,
                               lease_until=utcnow()+timedelta(seconds=LEASE_SECONDS))
            s.add(row)
            s.flush()
            return row.id, token, None

def locked(s, id, token):
    row = s.exec(svc.owned(Mutation).where(Mutation.id == id).with_for_update()).first()
    if row is None or row.state != "running" or row.lease_token != token:
        raise HTTPException(409, "Request lease changed; retry with the same key")
    row.lease_until = utcnow()+timedelta(seconds=LEASE_SECONDS)
    s.add(row)
    return row

def release(factory, id, token):
    with factory() as s:
        with s.begin():
            row = s.exec(svc.owned(Mutation).where(Mutation.id == id).with_for_update()).first()
            if row and row.state == "running" and row.lease_token == token:
                row.lease_until = utcnow()
                s.add(row)

def mutate(factory, key, fingerprint, operation):
    # REST mutations need no lease: effect and result commit in one transaction.
    with factory() as s:
        with s.begin():
            svc.guard_owner(s)
            if key:
                previous = s.exec(svc.owned(Mutation).where(Mutation.key == key).with_for_update()).first()
                if previous:
                    if previous.fingerprint != fingerprint:
                        raise HTTPException(409, "Idempotency-Key payload conflict")
                    if previous.state != "complete":
                        raise HTTPException(409, "request_in_progress")
                    return previous.result
            result = operation(s)
            if key:
                s.add(Mutation(id=str(uuid4()), owner_id=settings.demo_user_id, key=key,
                               fingerprint=fingerprint, state="complete", lease_token="",
                               lease_until=utcnow(), result=result))
            s.flush()
            return result
