"""Posting AMC 10, AMC 12 and AIME problems, or whole tests, by hand (backend/amc/posts.py).

A post is one problem (`kind: "problem"`, the default) or a whole test
(`kind: "test"`) whose `problems` each carry their statement, choices, answer
and solution; `/api/amc/posts/parse` reads a pasted test and answer key into
those problems for the page to check before posting.

Any signed-in account may post. Posts are shared by every account; only the
author, or an importer account (`temu`), may edit or delete one. A post that
cannot be saved comes back as `{"success": false, "message": ...}`.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.amc import posts
from backend.api.amc import can_import
from backend.api.guard import current_username
from backend.api.reply import fail, ok

router = APIRouter(tags=['amc-posts'])


def _may_edit(username, post):
    return post['author'] == username or can_import(username)


def _out(username, post):
    return {**post, 'can_edit': _may_edit(username, post)}


class ProblemBody(BaseModel):
    statement: str = ''
    choices: Optional[List[str]] = None
    answer: str = ''
    solution: str = ''


class PostBody(BaseModel):
    kind: str = 'problem'
    level: str
    title: str = ''
    statement: str = ''
    choices: Optional[List[str]] = None
    answer: str = ''
    solution: str = ''
    problems: Optional[List[ProblemBody]] = None


class ParseBody(BaseModel):
    level: str
    problems: str = ''
    key: str = ''


def _clean(body):
    """The post the body describes, as it will be stored; raises posts.Invalid."""
    if body.kind == 'test':
        return posts.clean_test(body.level, body.title, [p.model_dump() for p in body.problems or []])
    if body.kind != 'problem':
        raise posts.Invalid('A post is one problem or a whole test.')
    return posts.clean(body.level, body.title, body.statement, body.choices, body.answer, body.solution)


class SplitBody(BaseModel):
    statement: str = ''


@router.get('/api/amc/posts')
def listing(level: str = '', kind: str = '', username: str = Depends(current_username)):
    rows = posts.all_posts(level if level in posts.LEVELS else '', kind if kind in posts.KINDS else '')
    return ok(posts=[_out(username, p) for p in rows], levels=list(posts.LEVELS))


@router.get('/api/amc/posts/{post_id}')
def one(post_id: str, username: str = Depends(current_username)):
    post = posts.get(post_id)
    return ok(post=_out(username, post)) if post else fail('No such post.')


@router.post('/api/amc/posts/split')
def split(body: SplitBody, username: str = Depends(current_username)):
    """Pull the five choices out of a pasted AMC statement."""
    stem, choices = posts.split(body.statement)
    if not choices:
        return fail('No (A) to (E) choices found in the problem text.')
    return ok(statement=stem, choices=choices)


@router.post('/api/amc/posts/parse')
def parse(body: ParseBody, username: str = Depends(current_username)):
    """Read a pasted whole test and its answer key into problems to check and edit."""
    try:
        problems, issues = posts.parse(body.level, body.problems, body.key)
    except posts.Invalid as exc:
        return fail(str(exc))
    return ok(problems=problems, issues=issues)


@router.post('/api/amc/posts')
def create(body: PostBody, username: str = Depends(current_username)):
    try:
        post = _clean(body)
    except posts.Invalid as exc:
        return fail(str(exc))
    return ok(post=_out(username, posts.create(username, post)))


@router.put('/api/amc/posts/{post_id}')
def edit(post_id: str, body: PostBody, username: str = Depends(current_username)):
    have = posts.get(post_id)
    if not have:
        return fail('No such post.')
    if not _may_edit(username, have):
        return fail('Only the person who posted this can change it.')
    try:
        post = _clean(body)
    except posts.Invalid as exc:
        return fail(str(exc))
    return ok(post=_out(username, posts.update(post_id, post)))


@router.delete('/api/amc/posts/{post_id}')
def remove(post_id: str, username: str = Depends(current_username)):
    have = posts.get(post_id)
    if not have:
        return fail('No such post.')
    if not _may_edit(username, have):
        return fail('Only the person who posted this can delete it.')
    posts.delete(post_id)
    return ok()
