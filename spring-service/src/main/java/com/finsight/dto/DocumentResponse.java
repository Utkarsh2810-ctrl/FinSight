package com.finsight.dto;

import java.time.LocalDateTime;

public class DocumentResponse {
    private String documentId;
    private String filename;
    private String company;
    private Integer year;
    private String quarter;
    private Integer chunkCount;
    private LocalDateTime indexedAt;
    private String userId;

    public DocumentResponse() {}

    public static DocumentResponseBuilder builder() { return new DocumentResponseBuilder(); }

    public String getDocumentId() { return documentId; }
    public String getFilename() { return filename; }
    public String getCompany() { return company; }
    public Integer getYear() { return year; }
    public String getQuarter() { return quarter; }
    public Integer getChunkCount() { return chunkCount; }
    public LocalDateTime getIndexedAt() { return indexedAt; }
    public String getUserId() { return userId; }

    public static class DocumentResponseBuilder {
        private String documentId;
        private String filename;
        private String company;
        private Integer year;
        private String quarter;
        private Integer chunkCount;
        private LocalDateTime indexedAt;
        private String userId;

        public DocumentResponseBuilder documentId(String v) { this.documentId = v; return this; }
        public DocumentResponseBuilder filename(String v) { this.filename = v; return this; }
        public DocumentResponseBuilder company(String v) { this.company = v; return this; }
        public DocumentResponseBuilder year(Integer v) { this.year = v; return this; }
        public DocumentResponseBuilder quarter(String v) { this.quarter = v; return this; }
        public DocumentResponseBuilder chunkCount(Integer v) { this.chunkCount = v; return this; }
        public DocumentResponseBuilder indexedAt(LocalDateTime v) { this.indexedAt = v; return this; }
        public DocumentResponseBuilder userId(String v) { this.userId = v; return this; }

        public DocumentResponse build() {
            DocumentResponse r = new DocumentResponse();
            r.documentId = documentId; r.filename = filename;
            r.company = company; r.year = year; r.quarter = quarter;
            r.chunkCount = chunkCount; r.indexedAt = indexedAt; r.userId = userId;
            return r;
        }
    }
}