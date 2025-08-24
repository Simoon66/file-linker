# Telegram File Sharing Bot

## Overview

This is a Telegram bot designed for file sharing with admin controls and channel membership verification. The bot allows authorized administrators to upload files and generate shareable links, while requiring users to join specific channels before accessing shared files. The system supports bilingual messaging in Bengali and English, making it accessible to a diverse user base.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Technology**: Python-based Telegram bot using the `python-telegram-bot` library
- **Architecture Pattern**: Handler-based event processing with modular components
- **Rationale**: Provides robust async support and clean separation of concerns

### Authentication & Authorization
- **Admin Control**: Single admin user ID verification for file upload permissions
- **Channel Membership**: Multi-channel membership verification requirement before file access
- **Design**: Hardcoded admin ID and channel list for simplicity and security

### File Management
- **Storage Strategy**: Files are forwarded to a designated storage channel
- **Link Generation**: UUID-based short codes (8 characters) for shareable links
- **File Types**: Supports documents, photos, videos, audio, and other media types
- **Access Pattern**: Deep-linking through Telegram's start parameter system

### Database Design
- **Technology**: SQLite with single `files` table
- **Schema**: Stores file metadata, unique codes, message IDs, and upload tracking
- **Rationale**: Lightweight, serverless database suitable for bot's scale and requirements

### Messaging System
- **Localization**: Bilingual support (Bengali/English) with combined messages
- **User Flow**: Welcome messages, error handling, and status updates
- **Channel Integration**: Formatted channel lists for membership requirements

### Error Handling & Logging
- **Logging**: File-based and console logging with structured format
- **Error Recovery**: Graceful handling of Telegram API errors and membership check failures
- **User Feedback**: Clear error messages in both supported languages

## External Dependencies

### Core Services
- **Telegram Bot API**: Primary interface for bot operations and user interactions
- **Storage Channel**: Designated Telegram channel for file persistence and retrieval

### Third-Party Libraries
- **python-telegram-bot**: Official Telegram bot framework for Python
- **SQLite3**: Built-in Python database module for data persistence

### Environment Configuration
- **Bot Token**: 7918521477:AAE5Nm04alKrgNQ6LAl83xKyYmdgqJ_aPL4 (configured)
- **Admin User ID**: 7019013170 (single authorized administrator)  
- **Storage Channel ID**: -1002921970479 (target channel for file storage)
- **Required Channels**: @Anime_Hub_Official_1 (4 channels required for file access)

### File System
- **Database File**: Local SQLite database (`filebot.db`)
- **Log Files**: Application logging output (`bot.log`)