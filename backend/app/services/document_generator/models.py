from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentTable(BaseModel):
    caption: Optional[str] = None
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)


class DocumentCodeBlock(BaseModel):
    language: Optional[str] = "text"
    code: str = ""


class DocumentSection(BaseModel):
    heading: str
    level: int = 1
    paragraphs: List[str] = Field(default_factory=list)
    bullet_points: List[str] = Field(default_factory=list)
    numbered_list: List[str] = Field(default_factory=list)
    tables: List[DocumentTable] = Field(default_factory=list)
    code_blocks: List[DocumentCodeBlock] = Field(default_factory=list)
    page_break_after: bool = False


class DocumentStructure(BaseModel):
    title: str = "SOVA Technical Report"
    subtitle: Optional[str] = None
    author: Optional[str] = "SOVA Sovereign Intelligence"
    date: Optional[str] = None
    organization: Optional[str] = "SOVA Industrial Systems"
    confidentiality: Optional[str] = "Confidential - Air-Gapped Internal"
    summary: Optional[str] = None
    sections: List[DocumentSection] = Field(default_factory=list)
