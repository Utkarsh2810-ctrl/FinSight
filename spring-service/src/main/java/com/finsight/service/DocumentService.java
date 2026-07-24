package com.finsight.service;

import com.finsight.dto.DocumentRequest;
import com.finsight.dto.DocumentResponse;
import com.finsight.model.Document;
import com.finsight.model.User;
import com.finsight.repository.DocumentRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class DocumentService {

    private static final Logger log = LoggerFactory.getLogger(DocumentService.class);

    private final DocumentRepository documentRepository;
    private final AuthService authService;

    public DocumentService(DocumentRepository documentRepository, AuthService authService) {
        this.documentRepository = documentRepository;
        this.authService = authService;
    }

    /**
     * Called by the frontend after FastAPI successfully ingests a PDF.
     * Stores the document_id (from FastAPI) with user ownership info in H2.
     *
     * This is the integration seam between the two services:
     *   FastAPI  → returns document_id after ML indexing
     *   Frontend → calls this endpoint to register ownership
     *   Spring   → stores {user, document_id, metadata} in DB
     */
    public DocumentResponse registerDocument(String userEmail, DocumentRequest request) {
        if (documentRepository.existsByDocumentId(request.getDocumentId())) {
            throw new IllegalArgumentException(
                "Document already registered: " + request.getDocumentId()
            );
        }

        User user = authService.getCurrentUser(userEmail);

        Document doc = Document.builder()
                .documentId(request.getDocumentId())
                .filename(request.getFilename())
                .company(request.getCompany())
                .year(request.getYear())
                .quarter(request.getQuarter())
                .chunkCount(request.getChunkCount())
                .user(user)
                .build();

        doc = documentRepository.save(doc);
        log.info("Document registered: {} for user {}", doc.getDocumentId(), userEmail);

        return toResponse(doc);
    }

    public List<DocumentResponse> getUserDocuments(String userEmail) {
        User user = authService.getCurrentUser(userEmail);
        return documentRepository.findByUserOrderByIndexedAtDesc(user)
                .stream()
                .map(this::toResponse)
                .collect(Collectors.toList());
    }

    public void deleteDocument(String userEmail, String documentId) {
        User user = authService.getCurrentUser(userEmail);
        Document doc = documentRepository.findByDocumentIdAndUser(documentId, user)
                .orElseThrow(() -> new IllegalArgumentException(
                    "Document not found or not owned by user: " + documentId
                ));
        documentRepository.delete(doc);
        log.info("Document deleted: {} by user {}", documentId, userEmail);

        try {
            org.springframework.web.client.RestTemplate restTemplate = new org.springframework.web.client.RestTemplate();
            restTemplate.delete("http://localhost:8000/api/documents/" + documentId);
            log.info("Notified FastAPI backend to delete vector index for document {}", documentId);
        } catch (Exception e) {
            log.warn("Could not notify FastAPI backend of document deletion for {}: {}", documentId, e.getMessage());
        }
    }


    private DocumentResponse toResponse(Document doc) {
        return DocumentResponse.builder()
                .documentId(doc.getDocumentId())
                .filename(doc.getFilename())
                .company(doc.getCompany())
                .year(doc.getYear())
                .quarter(doc.getQuarter())
                .chunkCount(doc.getChunkCount())
                .indexedAt(doc.getIndexedAt())
                .userId(doc.getUser().getId().toString())
                .build();
    }
}