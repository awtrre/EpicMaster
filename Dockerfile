# Dockerfile (现在的版本)
FROM epic-base:v1

WORKDIR /app

# 1. 复制代码
COPY . .

# 2. 🔥 【关键一步】强制给启动脚本赋予执行权限！
RUN chmod +x entrypoint.sh

# 3. 创建并切换用户 (如果之前有这步)
RUN useradd -m -u 1000 appuser || true && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 6080

CMD ["./entrypoint.sh"]
