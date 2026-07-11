package com.finsight.repository;

import com.finsight.model.Document;
import com.finsight.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface DocumentRepository extends JpaRepository<Document, String> {
    List<Document> findByUserOrderByIndexedAtDesc(User user);
    Optional<Document> findByDocumentIdAndUser(String documentId, User user);
    boolean existsByDocumentId(String documentId);
}