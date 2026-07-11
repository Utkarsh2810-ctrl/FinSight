package com.finsight.dto;

public class AuthResponse {
    private String token;
    private String type = "Bearer";
    private String email;
    private String name;
    private String userId;

    public AuthResponse() {}

    public AuthResponse(String token, String email, String name, String userId) {
        this.token = token;
        this.email = email;
        this.name = name;
        this.userId = userId;
    }

    public static AuthResponseBuilder builder() { return new AuthResponseBuilder(); }

    public String getToken() { return token; }
    public String getType() { return type; }
    public String getEmail() { return email; }
    public String getName() { return name; }
    public String getUserId() { return userId; }
    public void setToken(String token) { this.token = token; }
    public void setEmail(String email) { this.email = email; }
    public void setName(String name) { this.name = name; }
    public void setUserId(String userId) { this.userId = userId; }

    public static class AuthResponseBuilder {
        private String token;
        private String email;
        private String name;
        private String userId;

        public AuthResponseBuilder token(String token) { this.token = token; return this; }
        public AuthResponseBuilder email(String email) { this.email = email; return this; }
        public AuthResponseBuilder name(String name) { this.name = name; return this; }
        public AuthResponseBuilder userId(String userId) { this.userId = userId; return this; }
        public AuthResponse build() { return new AuthResponse(token, email, name, userId); }
    }
}