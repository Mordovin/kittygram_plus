from rest_framework import serializers

import webcolors
import datetime as dt

from .models import Achievement, AchievementCat, Cat, Owner, CHOICES


class AchievementSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Achievement."""
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class CatSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Cat."""

    owner = serializers.SlugRelatedField(
        queryset=Owner.objects.all(),
        slug_field='last_name')
    achievements = AchievementSerializer(many=True)
    age = serializers.SerializerMethodField()
    color = serializers.ChoiceField(choices=CHOICES)

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year',
                  'owner', 'achievements', 'age')

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

    def create(self, validated_data):
        achievements = validated_data.pop('achievements')
        cat = Cat.objects.create(**validated_data)

        for achievement in achievements:
            current_achievement, created = Achievement.objects.get_or_create(
                **achievement)
            AchievementCat.objects.create(
                achievement=current_achievement, cat=cat)
        return cat

    def update(self, instance, validated_data):
        # Извлекаем новые достижения, если они есть
        achievements = validated_data.pop('achievements', [])
        # Обновляем поля экземпляра кота
        instance.name = validated_data.get('name', instance.name)
        instance.color = validated_data.get('color', instance.color)
        instance.birth_year = validated_data.get(
            'birth_year', instance.birth_year)
        instance.owner = validated_data.get('owner', instance.owner)
        instance.save()

        # Обновляем достижения
        if achievements:
            # Удаляем старые достижения
            instance.achievements.clear()

            # Добавляем новые достижения
            for achievement_data in achievements:
                current_achievement, created = (
                    Achievement.objects.get_or_create(**achievement_data))
                AchievementCat.objects.create(
                    achievement=current_achievement, cat=instance)

        return instance


class OwnerSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Owner."""

    cats = CatSerializer(many=True, required=False)

    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'full_name', 'cats')

    def create(self, validated_data):
        cats_data = validated_data.pop('cats', [])
        owner = Owner.objects.create(**validated_data)

        for cat_data in cats_data:
            cat_data['owner'] = owner
            Cat.objects.create(**cat_data)
        return owner

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.last_name = validated_data.get(
            'last_name', instance.last_name)
        instance.save()

        cats_data = validated_data.pop('cats', [])

        for cat_data in cats_data:
            cat_name = cat_data.get('name')
            cat, created = Cat.objects.get_or_create(
                name=cat_name, owner=instance)
            cat.color = cat_data.get('color', cat.color)
            cat.birth_year = cat_data.get('birth_year', cat.birth_year)
            cat.save()

        return instance


class CatListSerializer(serializers.ModelSerializer):
    color = serializers.ChoiceField(choices=CHOICES)

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color')
