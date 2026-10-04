# Ovamha demo hub FHIR server: HAPI FHIR R4, in-memory database (demo data resets on restart).
FROM hapiproject/hapi:latest
ENV HAPI_FHIR_FHIR_VERSION=R4 \
    HAPI_FHIR_ALLOW_EXTERNAL_REFERENCES=true \
    HAPI_FHIR_CORS_ALLOWED_ORIGIN=* \
    SPRING_DATASOURCE_URL=jdbc:h2:mem:ovamha \
    SPRING_DATASOURCE_USERNAME=sa \
    SPRING_DATASOURCE_PASSWORD= \
    SPRING_DATASOURCE_DRIVERCLASSNAME=org.h2.Driver \
    SPRING_JPA_PROPERTIES_HIBERNATE_DIALECT=ca.uhn.fhir.jpa.model.dialect.HapiFhirH2Dialect
EXPOSE 8080
