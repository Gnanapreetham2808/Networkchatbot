# Install LangChain Memory Management Dependencies

Write-Host "Installing LangChain and dependencies for chatbot memory management..." -ForegroundColor Cyan

# Upgrade pip first
python -m pip install --upgrade pip

# Install LangChain core packages
Write-Host "`nInstalling LangChain core packages..." -ForegroundColor Yellow
pip install langchain==0.3.7
pip install langchain-huggingface==0.1.2
pip install langchain-community==0.3.7
pip install sentence-transformers==3.3.1

# Verify installation
Write-Host "`nVerifying installation..." -ForegroundColor Yellow
python -c "import langchain; print(f'✓ LangChain {langchain.__version__} installed successfully')"
python -c "from langchain.memory import ConversationBufferMemory; print('✓ Memory modules available')"
python -c "import sentence_transformers; print('✓ Sentence Transformers available')"

Write-Host "`n✅ LangChain memory management installed successfully!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Configure memory settings in .env file" -ForegroundColor White
Write-Host "   CHATBOT_MEMORY_TYPE=window" -ForegroundColor Gray
Write-Host "   CHATBOT_MEMORY_WINDOW_SIZE=10" -ForegroundColor Gray
Write-Host "`n2. Restart the backend server:" -ForegroundColor White
Write-Host "   cd netops_backend" -ForegroundColor Gray
Write-Host "   python manage.py runserver" -ForegroundColor Gray
Write-Host "`n3. Test with a conversation - the bot will now remember context!" -ForegroundColor White
Write-Host "`nFor more details, see: MEMORY_MANAGEMENT.md" -ForegroundColor Cyan
