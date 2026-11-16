# chainsvc: mesh-eval test servisi (bkz. main.go)
FROM golang:1.26-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY main.go ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /chainsvc .

FROM scratch
COPY --from=build /chainsvc /chainsvc
USER 65532:65532
EXPOSE 9090
ENTRYPOINT ["/chainsvc"]
