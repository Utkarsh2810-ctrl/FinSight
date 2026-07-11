package com.finsight.dto;

public class DocumentRequest {
    private String documentId;
    private String filename;
    private String company;
    private Integer year;
    private String quarter;
    private Integer chunkCount;

    public String getDocumentId() { return documentId; }
    public String getFilename() { return filename; }
    public String getCompany() { return company; }
    public Integer getYear() { return year; }
    public String getQuarter() { return quarter; }
    public Integer getChunkCount() { return chunkCount; }
    public void setDocumentId(String documentId) { this.documentId = documentId; }
    public void setFilename(String filename) { this.filename = filename; }
    public void setCompany(String company) { this.company = company; }
    public void setYear(Integer year) { this.year = year; }
    public void setQuarter(String quarter) { this.quarter = quarter; }
    public void setChunkCount(Integer chunkCount) { this.chunkCount = chunkCount; }
}