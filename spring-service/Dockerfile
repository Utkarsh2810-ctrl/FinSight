# FinSight Auth Service — multi-stage Docker build
# Stage 1: Build with Maven
# Stage 2: Run the built jar on JRE 17

# --- Build stage ---
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn package -DskipTests -B

# --- Runtime stage ---
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

EXPOSE ${PORT:-8080}
CMD ["sh", "-c", "java -jar app.jar --server.port=${PORT:-8080}"]
