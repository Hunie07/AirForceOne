# DB 연결 방식

이 프로젝트는 다음 순서로 DB에 연결합니다.

1. `st.connection("weather", type="sql")`
2. 실패하면 `.streamlit/secrets.toml`의 `[mysql]` 로컬 설정

## 로컬만 쓸 때 예시

```toml
[mysql]
host = "localhost"
port = 3306
database = "weather_db"
user = "root"
password = "acorn1234"
charset = "utf8mb4"
```

## AWS RDS 쓸 때 예시

```toml
[connections.weather]
dialect = "mysql"
host = "your-rds-endpoint.ap-northeast-2.rds.amazonaws.com"
port = 3306
database = "weather_db"
username = "admin"
password = "your-password"
```
