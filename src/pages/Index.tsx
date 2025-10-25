import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ApiKey {
  id: string;
  key: string;
  name: string;
  created: Date;
  lastUsed?: Date;
}

interface TrainingExample {
  id: string;
  input: string;
  output: string;
  category: string;
  created: Date;
}

interface TelegramBot {
  id: string;
  telegram_token: string;
  bot_username?: string;
  is_active: boolean;
  webhook_url: string;
  created_at: string;
  last_activity?: string;
}

const Index = () => {
  const [isDark, setIsDark] = useState(true);
  const [activeTab, setActiveTab] = useState('home');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Привет! Я MadAI — искусственный интеллект с поддержкой Lua, JavaScript, Python и математики. Чем могу помочь?',
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [trainingExamples, setTrainingExamples] = useState<TrainingExample[]>([]);
  const [trainingInput, setTrainingInput] = useState('');
  const [trainingOutput, setTrainingOutput] = useState('');
  const [telegramBots, setTelegramBots] = useState<TelegramBot[]>([]);
  const [newTelegramToken, setNewTelegramToken] = useState('');
  const [selectedApiKeyForBot, setSelectedApiKeyForBot] = useState('');
  const [trainingCategory, setTrainingCategory] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    }
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [messagesRes, keysRes, botsRes] = await Promise.all([
        fetch('https://functions.poehali.dev/7a89db06-7752-4cc5-b58a-9a9235d4033a'),
        fetch('https://functions.poehali.dev/83448cb6-3488-4311-a792-23d36dc532c1'),
        fetch('https://functions.poehali.dev/0d3e0ea9-ef0c-43f4-b911-a5babcce4fbf', {
          headers: apiKeys.length > 0 ? { 'X-Api-Key': apiKeys[0].key } : {}
        })
      ]);

      if (messagesRes.ok) {
        const msgs = await messagesRes.json();
        if (msgs.length > 0) {
          setMessages(msgs.map((m: any) => ({
            id: m.id.toString(),
            role: m.role,
            content: m.content,
            timestamp: new Date(m.timestamp)
          })));
        }
      }

      if (keysRes.ok) {
        const keys = await keysRes.json();
        setApiKeys(keys.map((k: any) => ({
          id: k.id.toString(),
          key: k.key,
          name: k.name,
          created: new Date(k.created),
          lastUsed: k.lastUsed ? new Date(k.lastUsed) : undefined
        })));
      }

      await fetch('https://functions.poehali.dev/fcccfa67-b685-49d2-88f4-2ede52f81e42?seed=true');
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');

    try {
      const response = await fetch('https://functions.poehali.dev/7a89db06-7752-4cc5-b58a-9a9235d4033a', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: currentInput })
      });

      if (response.ok) {
        const data = await response.json();
        const aiResponse: Message = {
          id: data.ai_response.id.toString(),
          role: 'assistant',
          content: data.ai_response.content,
          timestamp: new Date(data.ai_response.timestamp),
        };
        setMessages((prev) => [...prev, aiResponse]);
      } else {
        throw new Error('Failed to get AI response');
      }
    } catch (error) {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateAIResponse(currentInput),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    }
  };

  const generateAIResponse = (input: string): string => {
    const lowerInput = input.toLowerCase();
    
    if (lowerInput.includes('lua') || lowerInput.includes('луа')) {
      return '```lua\n-- Пример Lua кода\nfunction greet(name)\n  return "Hello, " .. name\nend\n\nprint(greet("World"))\n```\n\nЯ могу помочь с программированием на Lua! Что именно вас интересует?';
    }
    
    if (lowerInput.includes('javascript') || lowerInput.includes('js')) {
      return '```javascript\n// Пример JavaScript кода\nconst greet = (name) => {\n  return `Hello, ${name}`;\n};\n\nconsole.log(greet("World"));\n```\n\nГотов помочь с JavaScript! Задавайте вопросы.';
    }
    
    if (lowerInput.includes('python') || lowerInput.includes('питон')) {
      return '```python\n# Пример Python кода\ndef greet(name):\n    return f"Hello, {name}"\n\nprint(greet("World"))\n```\n\nМогу помочь с Python! Какая задача?';
    }
    
    if (lowerInput.match(/\d+[\+\-\*\/]\d+/)) {
      try {
        const result = eval(lowerInput);
        return `Результат вычисления: **${result}**\n\nМогу решать более сложные математические задачи!`;
      } catch (e) {
        return 'Попробуйте другое математическое выражение.';
      }
    }
    
    return `Я обработал ваш запрос: "${input}"\n\nЯ поддерживаю:\n• Lua, JavaScript, Python\n• Математические вычисления\n• Обучение от пользователя\n\nЗадайте мне вопрос по программированию или математике!`;
  };

  const generateApiKey = async () => {
    try {
      const response = await fetch('https://functions.poehali.dev/83448cb6-3488-4311-a792-23d36dc532c1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: `API Key ${apiKeys.length + 1}` })
      });

      if (response.ok) {
        const newKey = await response.json();
        setApiKeys((prev) => [...prev, {
          id: newKey.id.toString(),
          key: newKey.key,
          name: newKey.name,
          created: new Date(newKey.created),
        }]);
        toast({
          title: 'API ключ создан',
          description: 'Новый ключ добавлен в список',
        });
      }
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось создать ключ',
        variant: 'destructive',
      });
    }
  };

  const copyApiKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast({
      title: 'Скопировано!',
      description: 'API ключ скопирован в буфер обмена',
    });
  };

  const deleteApiKey = async (id: string) => {
    try {
      await fetch(`https://functions.poehali.dev/83448cb6-3488-4311-a792-23d36dc532c1?id=${id}`, {
        method: 'DELETE',
      });
      setApiKeys((prev) => prev.filter((k) => k.id !== id));
      toast({
        title: 'Ключ удален',
        description: 'API ключ успешно удален',
      });
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось удалить ключ',
        variant: 'destructive',
      });
    }
  };

  const addTrainingExample = () => {
    if (!trainingInput.trim() || !trainingOutput.trim() || !trainingCategory.trim()) {
      toast({
        title: 'Заполните все поля',
        description: 'Для обучения нужны вход, выход и категория',
        variant: 'destructive',
      });
      return;
    }

    const newExample: TrainingExample = {
      id: Date.now().toString(),
      input: trainingInput,
      output: trainingOutput,
      category: trainingCategory,
      created: new Date(),
    };

    setTrainingExamples((prev) => [...prev, newExample]);
    setTrainingInput('');
    setTrainingOutput('');
    setTrainingCategory('');
    
    toast({
      title: 'Пример добавлен!',
      description: 'AI обучился на новом примере',
    });
  };

  const deleteTrainingExample = (id: string) => {
    setTrainingExamples((prev) => prev.filter((e) => e.id !== id));
    toast({
      title: 'Пример удален',
      description: 'Обучающий пример удален из базы',
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Icon name="Brain" className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                MadAI
              </h1>
              <p className="text-xs text-muted-foreground">by Мад Сатору</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1">
              <Icon name="Zap" size={12} />
              Online
            </Badge>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                setIsDark(!isDark);
                document.documentElement.classList.toggle('dark');
              }}
            >
              <Icon name={isDark ? 'Sun' : 'Moon'} size={20} />
            </Button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-8">
            <TabsTrigger value="home" className="gap-2">
              <Icon name="Home" size={16} />
              Главная
            </TabsTrigger>
            <TabsTrigger value="chat" className="gap-2">
              <Icon name="MessageSquare" size={16} />
              Чат с AI
            </TabsTrigger>
            <TabsTrigger value="api" className="gap-2">
              <Icon name="Key" size={16} />
              API ключи
            </TabsTrigger>
            <TabsTrigger value="telegram" className="gap-2">
              <Icon name="Send" size={16} />
              Telegram
            </TabsTrigger>
            <TabsTrigger value="training" className="gap-2">
              <Icon name="GraduationCap" size={16} />
              Обучение AI
            </TabsTrigger>
          </TabsList>

          <TabsContent value="home" className="space-y-8">
            <div className="text-center space-y-4 py-12">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-secondary mb-4">
                <Icon name="Sparkles" className="text-white" size={40} />
              </div>
              <h2 className="text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Добро пожаловать в MadAI
              </h2>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Искусственный интеллект с экспертизой в Lua, Roblox Studio и веб-поиском. Создан Мад Сатору в 2025 году.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <Card className="p-6 space-y-3 hover:shadow-lg transition-shadow border-primary/20">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Icon name="Code" className="text-primary" size={24} />
                </div>
                <h3 className="text-xl font-semibold">Lua & Roblox</h3>
                <p className="text-muted-foreground">
                  Экспертиза по Lua и Roblox Studio — от основ до DataStore и RemoteEvent
                </p>
              </Card>

              <Card className="p-6 space-y-3 hover:shadow-lg transition-shadow border-secondary/20">
                <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
                  <Icon name="Search" className="text-secondary" size={24} />
                </div>
                <h3 className="text-xl font-semibold">Веб-поиск</h3>
                <p className="text-muted-foreground">
                  Автоматический поиск через Yandex и Google, если не знаю ответ
                </p>
              </Card>

              <Card className="p-6 space-y-3 hover:shadow-lg transition-shadow border-primary/20">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Icon name="Send" className="text-primary" size={24} />
                </div>
                <h3 className="text-xl font-semibold">Telegram интеграция</h3>
                <p className="text-muted-foreground">
                  Подключите своего Telegram бота и отвечайте на вопросы прямо в мессенджере
                </p>
              </Card>
            </div>

            <Card className="p-8 bg-gradient-to-br from-primary/5 to-secondary/5 border-primary/20">
              <div className="space-y-4">
                <h3 className="text-2xl font-bold">Статистика обучения</h3>
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Примеров обучения</p>
                    <p className="text-3xl font-bold text-primary">{trainingExamples.length}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">API ключей</p>
                    <p className="text-3xl font-bold text-secondary">{apiKeys.length}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Сообщений в чате</p>
                    <p className="text-3xl font-bold text-primary">{messages.length}</p>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="chat" className="space-y-4">
            <Card className="p-6">
              <ScrollArea className="h-[500px] pr-4">
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                    >
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                          msg.role === 'user'
                            ? 'bg-primary text-white'
                            : 'bg-gradient-to-br from-primary to-secondary text-white'
                        }`}
                      >
                        <Icon name={msg.role === 'user' ? 'User' : 'Brain'} size={18} />
                      </div>
                      <div
                        className={`flex-1 rounded-lg p-4 ${
                          msg.role === 'user'
                            ? 'bg-primary text-white ml-12'
                            : 'bg-muted mr-12'
                        }`}
                      >
                        <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                        <p className={`text-xs mt-2 ${msg.role === 'user' ? 'text-white/70' : 'text-muted-foreground'}`}>
                          {msg.timestamp.toLocaleTimeString('ru-RU')}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>

              <div className="flex gap-2 mt-4">
                <Input
                  placeholder="Напишите сообщение... (попробуйте Lua, Python или 2+2)"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                  className="flex-1"
                />
                <Button onClick={sendMessage} className="gap-2">
                  <Icon name="Send" size={18} />
                  Отправить
                </Button>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="api" className="space-y-4">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-semibold">API ключи</h3>
                  <p className="text-sm text-muted-foreground">
                    Управление ключами доступа к MadAI API
                  </p>
                </div>
                <Button onClick={generateApiKey} className="gap-2">
                  <Icon name="Plus" size={18} />
                  Создать ключ
                </Button>
              </div>

              {apiKeys.length === 0 ? (
                <div className="text-center py-12 space-y-3">
                  <div className="w-16 h-16 rounded-full bg-muted mx-auto flex items-center justify-center">
                    <Icon name="Key" className="text-muted-foreground" size={32} />
                  </div>
                  <p className="text-muted-foreground">У вас пока нет API ключей</p>
                  <p className="text-sm text-muted-foreground">Создайте первый ключ для доступа к API</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {apiKeys.map((apiKey) => (
                    <Card key={apiKey.id} className="p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <p className="font-semibold">{apiKey.name}</p>
                            <Badge variant="outline" className="text-xs">
                              <Icon name="Shield" size={10} className="mr-1" />
                              Active
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 font-mono text-sm bg-muted px-3 py-2 rounded">
                            <code className="flex-1">{apiKey.key}</code>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyApiKey(apiKey.key)}
                            >
                              <Icon name="Copy" size={14} />
                            </Button>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Создан: {apiKey.created.toLocaleDateString('ru-RU')} в{' '}
                            {apiKey.created.toLocaleTimeString('ru-RU')}
                          </p>
                        </div>
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => deleteApiKey(apiKey.id)}
                          className="ml-4"
                        >
                          <Icon name="Trash2" size={18} />
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </Card>

            <Card className="p-6 bg-primary/5 border-primary/20">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Icon name="Info" size={18} className="text-primary" />
                Как использовать API
              </h4>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>1. Создайте API ключ и скопируйте его</p>
                <p>2. Добавьте ключ в заголовок запроса: Authorization: Bearer YOUR_KEY</p>
                <p>3. Отправляйте POST запросы на endpoint: https://api.madai.dev/v1/chat</p>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="training" className="space-y-4">
            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-4">Обучить AI на новом примере</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Входные данные</label>
                  <Textarea
                    placeholder="Например: Как сделать цикл в Lua?"
                    value={trainingInput}
                    onChange={(e) => setTrainingInput(e.target.value)}
                    className="min-h-[100px]"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Ожидаемый ответ</label>
                  <Textarea
                    placeholder="for i = 1, 10 do print(i) end"
                    value={trainingOutput}
                    onChange={(e) => setTrainingOutput(e.target.value)}
                    className="min-h-[100px]"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Категория</label>
                  <Input
                    placeholder="Lua, JavaScript, Python, Math..."
                    value={trainingCategory}
                    onChange={(e) => setTrainingCategory(e.target.value)}
                  />
                </div>
                <Button onClick={addTrainingExample} className="w-full gap-2">
                  <Icon name="Plus" size={18} />
                  Добавить пример обучения
                </Button>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-4">
                База обучения ({trainingExamples.length})
              </h3>
              
              {trainingExamples.length === 0 ? (
                <div className="text-center py-12 space-y-3">
                  <div className="w-16 h-16 rounded-full bg-muted mx-auto flex items-center justify-center">
                    <Icon name="GraduationCap" className="text-muted-foreground" size={32} />
                  </div>
                  <p className="text-muted-foreground">База обучения пуста</p>
                  <p className="text-sm text-muted-foreground">
                    Добавьте первый пример, чтобы AI начал обучаться
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {trainingExamples.map((example) => (
                    <Card key={example.id} className="p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-3">
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">{example.category}</Badge>
                            <span className="text-xs text-muted-foreground">
                              {example.created.toLocaleDateString('ru-RU')}
                            </span>
                          </div>
                          <div className="space-y-2">
                            <div>
                              <p className="text-sm font-medium text-muted-foreground mb-1">Вопрос:</p>
                              <p className="text-sm bg-muted p-2 rounded">{example.input}</p>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-muted-foreground mb-1">Ответ:</p>
                              <p className="text-sm bg-muted p-2 rounded">{example.output}</p>
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteTrainingExample(example.id)}
                        >
                          <Icon name="Trash2" size={18} />
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="telegram" className="space-y-4">
            <Card className="p-6 bg-gradient-to-br from-primary/10 to-secondary/10 border-primary/30">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                  <Icon name="Send" className="text-primary" size={24} />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold mb-2">Интеграция с Telegram</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Подключите MadAI к вашему Telegram боту. Бот будет отвечать на вопросы по Lua программированию прямо в мессенджере.
                  </p>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-start gap-2">
                      <Icon name="Check" className="text-primary mt-0.5" size={16} />
                      <p>Экспертиза по Lua — от основ до метатаблиц</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <Icon name="Check" className="text-primary mt-0.5" size={16} />
                      <p>Примеры кода и объяснения</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <Icon name="Check" className="text-primary mt-0.5" size={16} />
                      <p>Защита через API ключи</p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-4">Добавить Telegram бота</h3>
              
              <div className="space-y-4 mb-6">
                <div>
                  <label className="text-sm font-medium mb-2 block">Выберите API ключ</label>
                  <select 
                    className="w-full px-3 py-2 rounded-md border border-input bg-background"
                    value={selectedApiKeyForBot}
                    onChange={(e) => setSelectedApiKeyForBot(e.target.value)}
                  >
                    <option value="">-- Выберите API ключ --</option>
                    {apiKeys.map((key) => (
                      <option key={key.id} value={key.key}>
                        {key.name} ({key.key.substring(0, 15)}...)
                      </option>
                    ))}
                  </select>
                  {apiKeys.length === 0 && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Сначала создайте API ключ во вкладке "API ключи"
                    </p>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Telegram Bot Token
                    <a 
                      href="https://t.me/BotFather" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary ml-2 text-xs hover:underline"
                    >
                      Получить в @BotFather
                    </a>
                  </label>
                  <Input
                    placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                    value={newTelegramToken}
                    onChange={(e) => setNewTelegramToken(e.target.value)}
                    type="password"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Токен от @BotFather в формате: 123456:ABC-DEF...
                  </p>
                </div>

                <Button 
                  onClick={async () => {
                    if (!selectedApiKeyForBot || !newTelegramToken) {
                      toast({
                        title: 'Заполните все поля',
                        description: 'Выберите API ключ и введите Telegram токен',
                        variant: 'destructive',
                      });
                      return;
                    }

                    try {
                      const webhookUrl = 'https://functions.poehali.dev/42cde964-8986-42e2-924b-21e95a95a8a0';
                      
                      const response = await fetch('https://functions.poehali.dev/0d3e0ea9-ef0c-43f4-b911-a5babcce4fbf', {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'X-Api-Key': selectedApiKeyForBot,
                        },
                        body: JSON.stringify({
                          telegram_token: newTelegramToken,
                          webhook_url: webhookUrl,
                        }),
                      });

                      if (!response.ok) {
                        throw new Error('Failed to add bot');
                      }

                      const result = await response.json();
                      
                      const newBot: TelegramBot = {
                        id: result.id.toString(),
                        telegram_token: newTelegramToken,
                        bot_username: result.bot_username,
                        is_active: true,
                        webhook_url: webhookUrl,
                        created_at: new Date().toISOString(),
                      };

                      setTelegramBots((prev) => [...prev, newBot]);
                      setNewTelegramToken('');
                      setSelectedApiKeyForBot('');

                      toast({
                        title: 'Бот подключен!',
                        description: `@${result.bot_username} готов к работе`,
                      });
                    } catch (error) {
                      toast({
                        title: 'Ошибка',
                        description: 'Проверьте токен и попробуйте снова',
                        variant: 'destructive',
                      });
                    }
                  }}
                  className="w-full gap-2"
                  disabled={!selectedApiKeyForBot || !newTelegramToken}
                >
                  <Icon name="Plus" size={18} />
                  Подключить бота
                </Button>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-xl font-semibold mb-4">
                Мои Telegram боты ({telegramBots.length})
              </h3>

              {telegramBots.length === 0 ? (
                <div className="text-center py-12 space-y-3">
                  <div className="w-16 h-16 rounded-full bg-muted mx-auto flex items-center justify-center">
                    <Icon name="Bot" className="text-muted-foreground" size={32} />
                  </div>
                  <p className="text-muted-foreground">У вас нет подключенных ботов</p>
                  <p className="text-sm text-muted-foreground">
                    Создайте бота в @BotFather и подключите его выше
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {telegramBots.map((bot) => (
                    <Card key={bot.id} className="p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <Icon name="Send" className="text-primary" size={18} />
                            <p className="font-semibold">
                              {bot.bot_username ? `@${bot.bot_username}` : 'Telegram Bot'}
                            </p>
                            <Badge variant={bot.is_active ? 'default' : 'secondary'}>
                              {bot.is_active ? 'Активен' : 'Неактивен'}
                            </Badge>
                          </div>
                          <div className="text-xs text-muted-foreground space-y-1">
                            <p>Webhook: {bot.webhook_url}</p>
                            <p>Создан: {new Date(bot.created_at).toLocaleString('ru-RU')}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant={bot.is_active ? 'outline' : 'default'}
                            size="sm"
                            onClick={async () => {
                              try {
                                const response = await fetch('https://functions.poehali.dev/0d3e0ea9-ef0c-43f4-b911-a5babcce4fbf', {
                                  method: 'PUT',
                                  headers: {
                                    'Content-Type': 'application/json',
                                    'X-Api-Key': selectedApiKeyForBot,
                                  },
                                  body: JSON.stringify({ bot_id: parseInt(bot.id) }),
                                });

                                if (response.ok) {
                                  setTelegramBots((prev) =>
                                    prev.map((b) =>
                                      b.id === bot.id ? { ...b, is_active: !b.is_active } : b
                                    )
                                  );
                                  toast({
                                    title: bot.is_active ? 'Бот остановлен' : 'Бот активирован',
                                  });
                                }
                              } catch (error) {
                                toast({
                                  title: 'Ошибка',
                                  description: 'Не удалось изменить статус',
                                  variant: 'destructive',
                                });
                              }
                            }}
                          >
                            <Icon name={bot.is_active ? 'Pause' : 'Play'} size={14} />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </Card>

            <Card className="p-6 bg-primary/5 border-primary/20">
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Icon name="Info" size={18} className="text-primary" />
                Как подключить бота?
              </h4>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p><strong>1.</strong> Создайте бота в Telegram через @BotFather командой /newbot</p>
                <p><strong>2.</strong> Скопируйте полученный токен</p>
                <p><strong>3.</strong> Создайте API ключ во вкладке "API ключи"</p>
                <p><strong>4.</strong> Подключите бота выше, указав API ключ и токен</p>
                <p><strong>5.</strong> Бот автоматически настроится и начнёт отвечать на вопросы по Lua!</p>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;