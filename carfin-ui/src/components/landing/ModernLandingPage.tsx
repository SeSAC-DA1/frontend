'use client';

import { useState, useEffect } from 'react';
import { Container } from '@/components/design-system/layout/Container';
import { EnhancedButton } from '@/components/design-system/forms/EnhancedButton';
import {
  Car,
  ArrowRight,
  MessageCircle,
  Play,
  CheckCircle,
  Sparkles,
  Zap,
  Shield,
  TrendingUp,
  Users,
  Star,
  ChevronDown,
  Brain,
  Target,
  Globe
} from 'lucide-react';

interface ModernLandingPageProps {
  onGetStarted: () => void;
}

export function ModernLandingPage({ onGetStarted }: ModernLandingPageProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const features = [
    {
      icon: <Brain className="w-8 h-8" />,
      title: "AI 맞춤 분석",
      description: "3개 전문 AI가 협업하여 당신만의 완벽한 차량을 찾습니다",
      color: "from-blue-500 to-purple-600"
    },
    {
      icon: <Target className="w-8 h-8" />,
      title: "정확한 매칭",
      description: "실시간 데이터와 사용자 패턴 학습으로 98% 만족도 달성",
      color: "from-green-500 to-blue-600"
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: "투명한 정보",
      description: "숨겨진 비용 없이 모든 차량 정보를 투명하게 공개합니다",
      color: "from-purple-500 to-pink-600"
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "빠른 상담",
      description: "평균 3분만에 최적의 차량과 금융 솔루션을 제안합니다",
      color: "from-yellow-500 to-orange-600"
    }
  ];

  const stats = [
    { number: "15만+", label: "분석 완료", icon: <TrendingUp className="w-5 h-5" /> },
    { number: "98%", label: "만족도", icon: <Star className="w-5 h-5" /> },
    { number: "3분", label: "평균 시간", icon: <Zap className="w-5 h-5" /> },
    { number: "24/7", label: "AI 상담", icon: <MessageCircle className="w-5 h-5" /> }
  ];

  const steps = [
    {
      number: "01",
      title: "AI와 대화",
      description: "간단한 질문으로 당신의 필요를 파악합니다",
      icon: <MessageCircle className="w-8 h-8" />,
      color: "text-blue-600"
    },
    {
      number: "02",
      title: "차량 선택",
      description: "AI가 선별한 차량 중에서 선택하세요",
      icon: <Car className="w-8 h-8" />,
      color: "text-green-600"
    },
    {
      number: "03",
      title: "분석 결과",
      description: "오각형 차트로 한눈에 보는 차량 분석",
      icon: <Target className="w-8 h-8" />,
      color: "text-purple-600"
    },
    {
      number: "04",
      title: "금융 상담",
      description: "최적의 금융 상품까지 한번에 해결",
      icon: <CheckCircle className="w-8 h-8" />,
      color: "text-orange-600"
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-md border-b border-gray-100 z-50">
        <Container>
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl flex items-center justify-center">
                <Car className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold text-gray-900">CarFin AI</span>
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
                  Beta
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <EnhancedButton
                variant="ghost"
                size="sm"
              >
                서비스 소개
              </EnhancedButton>
              <EnhancedButton
                variant="primary"
                size="sm"
                onClick={onGetStarted}
                icon={<Sparkles className="w-4 h-4" />}
              >
                시작하기
              </EnhancedButton>
            </div>
          </div>
        </Container>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <Container>
          <div className={`text-center max-w-4xl mx-auto transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}>

            {/* Hero Badge */}
            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full mb-8">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-medium">AI로 찾는 완벽한 중고차</span>
            </div>

            {/* Hero Title */}
            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                3분만에 찾는
              </span>
              <br />
              당신의 차량
            </h1>

            {/* Hero Description */}
            <p className="text-xl md:text-2xl text-gray-600 mb-12 leading-relaxed">
              3개의 전문 AI가 협업하여 당신의 취향을 학습하고,<br />
              투명한 데이터로 최적의 중고차를 추천합니다.
            </p>

            {/* Hero CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <EnhancedButton
                variant="primary"
                size="xl"
                onClick={onGetStarted}
                icon={<MessageCircle className="w-6 h-6" />}
                className="shadow-xl shadow-blue-200"
              >
                AI 상담 시작하기
              </EnhancedButton>

              <EnhancedButton
                variant="outline"
                size="xl"
                icon={<Play className="w-6 h-6" />}
              >
                데모 보기
              </EnhancedButton>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {stats.map((stat, index) => (
                <div
                  key={index}
                  className={`bg-white rounded-2xl p-6 shadow-lg border border-gray-100 transition-all duration-500 ${
                    isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                  }`}
                  style={{ transitionDelay: `${index * 150}ms` }}
                >
                  <div className="flex items-center justify-center gap-2 text-blue-600 mb-2">
                    {stat.icon}
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-1">{stat.number}</div>
                  <div className="text-sm text-gray-600">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </Container>

        {/* Scroll Indicator */}
        <div className="text-center mt-16">
          <ChevronDown className="w-6 h-6 text-gray-400 mx-auto animate-bounce" />
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <Container>
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              AI의 힘으로 완전히 새로운 경험
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              전통적인 중고차 매매의 한계를 뛰어넘어, AI 기술로 투명하고 정확한 차량 매칭을 제공합니다.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-gradient-to-br from-white to-gray-50 rounded-3xl p-8 border border-gray-100 hover:shadow-2xl transition-all duration-300 group"
              >
                <div className={`w-16 h-16 bg-gradient-to-r ${feature.color} rounded-2xl flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-4">{feature.title}</h3>
                <p className="text-gray-600 text-lg leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </Container>
      </section>

      {/* Process Section */}
      <section className="py-24 bg-gradient-to-br from-gray-50 to-blue-50">
        <Container>
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              간단한 4단계로 완료
            </h2>
            <p className="text-xl text-gray-600">
              복잡한 절차 없이 AI가 모든 것을 자동으로 처리합니다
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="text-center group">
                {/* Step Number */}
                <div className="relative mb-6">
                  <div className="w-20 h-20 bg-white rounded-full shadow-lg flex items-center justify-center mx-auto border-4 border-gray-100 group-hover:border-blue-200 transition-all duration-300">
                    <span className="text-2xl font-bold text-gray-400">{step.number}</span>
                  </div>
                  <div className={`absolute inset-0 w-20 h-20 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full opacity-0 group-hover:opacity-10 transition-opacity duration-300 mx-auto`} />
                </div>

                {/* Step Icon */}
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4 ${step.color} bg-white shadow-sm`}>
                  {step.icon}
                </div>

                {/* Step Content */}
                <h3 className="text-xl font-bold text-gray-900 mb-3">{step.title}</h3>
                <p className="text-gray-600">{step.description}</p>

                {/* Connection Line */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-10 left-1/2 w-full h-px bg-gradient-to-r from-gray-200 to-transparent transform translate-x-10" />
                )}
              </div>
            ))}
          </div>
        </Container>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-blue-600 to-purple-700 text-white">
        <Container>
          <div className="text-center max-w-4xl mx-auto">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              지금 시작해서 완벽한 차량을 찾아보세요
            </h2>
            <p className="text-xl mb-12 opacity-90">
              15만 명이 이미 CarFin AI와 함께 최적의 차량을 찾았습니다.<br />
              당신도 3분만에 시작할 수 있어요.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <EnhancedButton
                variant="secondary"
                size="xl"
                onClick={onGetStarted}
                icon={<Sparkles className="w-6 h-6" />}
                className="bg-white text-blue-700 hover:bg-gray-50 shadow-xl"
              >
                무료로 시작하기
              </EnhancedButton>

              <EnhancedButton
                variant="outline"
                size="xl"
                className="border-white text-white hover:bg-white/10"
              >
                더 알아보기
              </EnhancedButton>
            </div>
          </div>
        </Container>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-gray-900 text-white">
        <Container>
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center gap-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                <Car className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-semibold">CarFin AI</span>
            </div>

            <div className="text-center md:text-right">
              <p className="text-gray-400 text-sm mb-1">
                AI 기반 중고차 추천 플랫폼
              </p>
              <p className="text-gray-500 text-xs">
                © 2025 CarFin AI. All rights reserved.
              </p>
            </div>
          </div>
        </Container>
      </footer>
    </div>
  );
}