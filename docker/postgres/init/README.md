# Docker PostgreSQL Initialization

This directory contains initialization scripts that run when the PostgreSQL container starts for the first time.

## Files

- `init.sql` - Creates the initial database schema and extensions

## Usage

Scripts in this directory are executed in alphabetical order when the container is created.
