---
title: "{{title}}"
type: moc
layer: "{{layer}}"
status: draft
created: {{date}}
updated: {{date}}
---

# {{title}}

## 개요

> 이 계층의 역할과 책임을 1-2문장으로 설명.

## 문서 목록

```dataview
TABLE status, updated, tags
FROM "{{folder}}"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 ADR

```dataview
LIST
FROM "docs/architecture/decisions"
WHERE contains(impacts, this.file.link)
SORT date DESC
```
