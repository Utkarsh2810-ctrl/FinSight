package com.finsight.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "documents")
public class Document {

    @Id
    @Column(nullable = false, unique = true)
    private String documentId;

    @Column(nullable = false)
    private String filename;

    @Column(nullable = false)
    private String company;

    @Column(name = "fiscal_year", nullable = false)
    private Integer year;

    @Column(nullable = false)
    private String quarter;

    private Integer chunkCount;

    @Column(nullable = false)
    private LocalDateTime indexedAt;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @PrePersist
    protected void onCreate() { this.indexedAt = LocalDateTime.now(); }

    public String getDocumentId() { return documentId; }
    public String getFilename() { return filename; }
    public String getCompany() { return company; }
    public Integer getYear() { return year; }
    public String getQuarter() { return quarter; }
    public Integer getChunkCount() { return chunkCount; }
    public LocalDateTime getIndexedAt() { return indexedAt; }
    public User getUser() { return user; }

    public void setDocumentId(String documentId) { this.documentId = documentId; }
    public void setFilename(String filename) { this.filename = filename; }
    public void setCompany(String company) { this.company = company; }
    public void setYear(Integer year) { this.year = year; }
    public void setQuarter(String quarter) { this.quarter = quarter; }
    public void setChunkCount(Integer chunkCount) { this.chunkCount = chunkCount; }
    public void setIndexedAt(LocalDateTime indexedAt) { this.indexedAt = indexedAt; }
    public void setUser(User user) { this.user = user; }

    public static DocumentBuilder builder() { return new DocumentBuilder(); }

    public static class DocumentBuilder {
        private String documentId;
        private String filename;
        private String company;
        private Integer year;
        private String quarter;
        private Integer chunkCount;
        private User user;

        public DocumentBuilder documentId(String v) { this.documentId = v; return this; }
        public DocumentBuilder filename(String v) { this.filename = v; return this; }
        public DocumentBuilder company(String v) { this.company = v; return this; }
        public DocumentBuilder year(Integer v) { this.year = v; return this; }
        public DocumentBuilder quarter(String v) { this.quarter = v; return this; }
        public DocumentBuilder chunkCount(Integer v) { this.chunkCount = v; return this; }
        public DocumentBuilder user(User v) { this.user = v; return this; }

        public Document build() {
            Document d = new Document();
            d.documentId = documentId; d.filename = filename;
            d.company = company; d.year = year; d.quarter = quarter;
            d.chunkCount = chunkCount; d.user = user;
            return d;
        }
    }
}