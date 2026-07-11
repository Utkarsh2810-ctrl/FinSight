package com.finsight.controller;

import com.finsight.dto.DocumentRequest;
import com.finsight.dto.DocumentResponse;
import com.finsight.service.DocumentService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    /**
     * POST /api/documents
     * Protected — requires valid JWT.
     *
     * Called by the frontend AFTER FastAPI successfully ingests a PDF.
     * Flow:
     *   1. Frontend → POST /api/upload (FastAPI) → gets document_id
     *   2. Frontend → POST /api/documents (Spring) → registers ownership in DB
     *
     * Body: { documentId, filename, company, year, quarter, chunkCount }
     */
    @PostMapping
    public ResponseEntity<DocumentResponse> registerDocument(
            @AuthenticationPrincipal UserDetails userDetails,
            @Valid @RequestBody DocumentRequest request
    ) {
        try {
            DocumentResponse response = documentService.registerDocument(
                userDetails.getUsername(), request
            );
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * GET /api/documents
     * Protected — returns all documents belonging to the authenticated user.
     * This is what the frontend document selector reads from.
     */
    @GetMapping
    public ResponseEntity<List<DocumentResponse>> getUserDocuments(
            @AuthenticationPrincipal UserDetails userDetails
    ) {
        List<DocumentResponse> docs = documentService.getUserDocuments(userDetails.getUsername());
        return ResponseEntity.ok(docs);
    }

    /**
     * DELETE /api/documents/{documentId}
     * Protected — user can only delete their own documents.
     * Note: this removes the DB record only. The FastAPI vector index
     * is not automatically cleaned — add a call to FastAPI DELETE endpoint
     * here in production.
     */
    @DeleteMapping("/{documentId}")
    public ResponseEntity<Map<String, String>> deleteDocument(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable String documentId
    ) {
        try {
            documentService.deleteDocument(userDetails.getUsername(), documentId);
            return ResponseEntity.ok(Map.of("status", "deleted", "documentId", documentId));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }
}