# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## 项目启动指南

每次新会话开始时，先阅读 `docs/` 目录中的最新技术文档（按日期判断），了解项目当前架构和最新变更。

## 代码变更规则

每次修改前端代码（`frontend/`）或后端代码（`backend/`）后，必须检查 `start.bat` 是否需要同步更新，包括但不限于：

- 新增/删除依赖（Python pip 包、npm 包）
- 新增/删除启动步骤（如数据库初始化、环境检查）
- 端口或主机配置变更
- 新增/删除目录或文件路径引用
- 构建命令变化

如果 `start.bat` 需要更新，在代码变更完成后同步修改。
