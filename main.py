import pyswip
from subprocess import Popen, PIPE, STDOUT
from datetime import date
from dataclasses import dataclass, field
import prolog1 as prolog
from thefuzz import fuzz, process
import tempfile
import os

DEBUG = print if False else lambda *_, **kw: None

prolog_lines = []

query_prolog = pyswip.Prolog()


def add_rule(line):
    prolog_lines.append(line)
    prolog.Rule(line)
    query_prolog.assertz(line)


def add_term(line):
    prolog_lines.append(line)
    prolog.Term(line)
    query_prolog.assertz(line)


multiplayer_term = "has_multiplayer(%s)"
still_updates_term = "still_updates(%s)"
has_open_world_term = "is_open_world(%s)"
is_game_of_the_year_term = "is_game_of_the_year(%s)"

still_produced_term = "still_produced(%s)"
is_portable_term = "is_portable(%s)"
supports_vr_term = "supports_vr(%s)"

ganre_term = "genre(%s, %s)"
released_on_term = "released_on(%s, %s)"
can_emulate_term = "can_emulate(%s, %s)"
released_term = "released(%s, %s)"

rules = [
    """
    can_be_run_on(X, Y):- released_on(X, Y)
    can_be_run_on(X, Y):- can_emulate(Y, Z), can_be_run_on(X, Z)
    """,

    "still_available(X):- still_produced(Y), can_be_run_on(X, Y), still_updates(X)",

    "platform_worth_buying(X):- still_produced(X), can_be_run_on(Y, X), is_game_of_the_year(Y)"
]


@dataclass(repr=False)
class Platform:
    name: str
    can_emulate: list = field(default_factory=list)
    still_produced: bool = True
    is_portable: bool = False
    supports_vr: bool = False

    def __post_init__(self):
        if self.is_portable:
            add_term(is_portable_term % self.name)
            DEBUG(is_portable_term % self.name)
        if self.supports_vr:
            add_term(supports_vr_term % self.name)
            DEBUG(supports_vr_term % self.name)
        if self.still_produced:
            add_term(still_produced_term % self.name)
            DEBUG(still_produced_term % self.name)
        for p in self.can_emulate:
            add_term(can_emulate_term % (self.name, p.name))
            DEBUG(can_emulate_term % (self.name, p.name))

    def __repr__(self):
        return self.name


@dataclass(repr=False)
class Game:
    name: str
    genre: str
    has_multiplayer: bool = False
    still_updates: bool = False
    has_open_world: bool = False
    is_game_of_the_year: bool = False
    release_year: date = "2000"
    released_on: list = field(default_factory=list)

    def __post_init__(self):
        add_term(ganre_term % (self.name, self.genre))
        DEBUG(ganre_term % (self.name, self.genre))

        if self.has_multiplayer:
            add_term(multiplayer_term % self.name)
            DEBUG(multiplayer_term % self.name)
        if self.still_updates:
            add_term(still_updates_term % self.name)
            DEBUG(still_updates_term % self.name)
        if self.is_game_of_the_year:
            add_term(is_game_of_the_year_term % self.name)
            DEBUG(multiplayer_term % self.name)
        if self.has_open_world:
            add_term(has_open_world_term % self.name)
            DEBUG(has_open_world_term % self.name)
        for p in self.released_on:
            add_term(released_on_term % (self.name, p.name))
            DEBUG(released_on_term % (self.name, p.name))

        add_term(released_term % (self.name, self.release_year))
        DEBUG(released_term % (self.name, self.release_year))
        DEBUG()

    def __repr__(self):
        return self.name


Mobile = Platform("mobile", is_portable=True)
Switch = Platform("switch", is_portable=True)
PS3 = Platform("ps3", still_produced=False)

PC = Platform("pc",
              can_emulate=[Mobile, PS3],
              supports_vr=True
              )
PS4 = Platform("ps4",
               can_emulate=[PS3],
               supports_vr=True
               )
XBox = Platform("xbox", supports_vr=True)


GTA5 = Game(
    name="gta5",
    genre="action",
    has_multiplayer=True,
    still_updates=True,
    has_open_world=True,
    is_game_of_the_year=True,
    release_year="2013",
    released_on=[PC, PS3, XBox]
)

Worms_revolution = Game(
    name="worms_revolution",
    genre="strategy",
    has_multiplayer=True,
    release_year="2012",
    released_on=[PC, PS3, XBox]
)

Animal_crossing = Game(
    name="animal_crossing",
    genre="simulation",
    has_multiplayer=True,
    still_updates=True,
    has_open_world=True,
    release_year="2020",
    released_on=[Switch]
)

Dont_starve = Game(
    name="dont_starve",
    genre="survival",
    still_updates=True,
    has_open_world=True,
    release_year="2013",
    released_on=[PC, PS3, Mobile, Switch, XBox]
)

GOW = Game(
    name="god_of_war",
    genre="adventure",
    has_open_world=True,
    is_game_of_the_year=True,
    release_year="2018",
    released_on=[PS4]
)

Bloodborne = Game(
    name="bloodborne",
    genre="adventure",
    release_year="2015",
    released_on=[PS4]
)

Zelda = Game(
    name="zelda",
    genre="adventure",
    release_year="2017",
    released_on=[Switch]
)


Minecraft = Game(
    name="minecraft",
    genre="survival",
    has_multiplayer=True,
    still_updates=True,
    has_open_world=True,
    is_game_of_the_year=False,
    release_year="2011",
    released_on=[PC, PS4, Mobile, Switch, XBox]
)

CivilizationVi = Game(
    name="civilization_vi",
    genre="strategy",
    has_multiplayer=True,
    still_updates=False,
    has_open_world=True,
    is_game_of_the_year=True,
    release_year="2016",
    released_on=[PC, PS3, Mobile, XBox]
)

StardewValley = Game(
    name="stardew_valley",
    genre="simulation",
    has_multiplayer=True,
    still_updates=True,
    has_open_world=True,
    is_game_of_the_year=False,
    release_year="2016",
    released_on=[PC, Mobile, Switch, XBox]
)

for r in rules:
    lines = list(map(lambda s: s.strip(), r.split("\n")))
    for line in lines:
        if line != "":
            DEBUG(line, end="\n\n")
            add_rule(line)


def flattenInnerLists(d):
    flattened = {}
    for key, value in d.items():
        if type(key) == tuple:
            for item in key:
                flattened[item] = value
        elif type(key) == str and ";" in key:
            for item in key.split(";"):
                flattened[item.strip()] = value
        else:
            flattened[key] = value
    return flattened


platforms = flattenInnerLists(
    {"пк; pc": PC, "ps4; пс4; плойка; плейстейшен; sony playstation 4": PS4,
     "нинтендо; свитч; switch; nintendo switch": Switch,
     "телефон; мобила; смартфон": Mobile, "xbox; иксбокс": XBox,
     "ps3; пс3; sony playstation 3": PS3, })

aux = flattenInnerLists({"у меня есть; я купил; я играю на": True, "у меня нет": False, })

platform_having_tokens = [[(t + " " + p, obj, sign) for p, obj in platforms.items()]
                          for t, sign in aux.items()]

genres = flattenInnerLists(
    {"приключения; бродилки; квесты; адвенчуры": "adventure",
     "стратегия; головоломки; пошаговая; пошаговая стратегия": "strategy",
     "выживание; хардкор; повыживать": "survival",
     "боевик; чтобы крч взрывалось всё": "action", "симулятор": "simulation", })

aux = flattenInnerLists({
    "я люблю; мне нравятся; мне нравится жанр; я хочу поиграть в": True,
    "Я не люблю; мне не нравится жанр": False,
})
genres_having_tokens = [[(t + " " + p, obj, sign) for p, obj in genres.items()]
                        for t, sign in aux.items()]

companies = flattenInnerLists({"одному; в одиночку; соло": False, "с друзьями; вместе с кем-то; с братом": True,
                               "с сестрой; онлайн; с кем-то": True})

aux = flattenInnerLists({
    "я хочу поиграть; мне нравятся играть; хочется поиграть": True,
    "мне не нравится играть; я не хочу играть": False,
})
companies_having_tokens = [[(t + " " + p, (obj if sign else not obj)) for p, obj in companies.items()]
                           for t, sign in aux.items()]


def flattenInnerMap(arr):
    flattened = {}
    for subarr in arr:
        for key, *other in subarr:
            flattened[key] = other
    return flattened


platform_having_tokens = flattenInnerMap(platform_having_tokens)
genres_having_tokens = flattenInnerMap(genres_having_tokens)
companies_having_tokens = flattenInnerMap(companies_having_tokens)
groups = [
    platform_having_tokens,
    genres_having_tokens,
    companies_having_tokens
]


def split_based_on_semantics(text):
    sentences = list(map(lambda s: s.strip(), text.split(".")))
    semantics = {}
    all_combined = []
    for i, sentence in enumerate(sentences):
        group_index, champ_token, champ_perc = None, None, -1
        for index, group in enumerate(groups):
            token, percentage = process.extractOne(sentence, group.keys())
            all_combined.append((i, index, token, percentage))
            if percentage > champ_perc:
                champ_perc = percentage
                champ_token = token
                group_index = index
        semantics[i] = (group_index, groups[group_index][champ_token])
    return semantics


def semantics_to_facts(semantics):
    nonesense = {}

    has_platforms = []
    doesnt_have_platforms = []

    wants_solo = None

    suitable_genres = []
    prohibited_genres = []

    for (group, result) in semantics.values():
        if group == 0:
            platform, has_it, *_ = result

            if has_it:
                has_platforms.append(platform)
            else:
                doesnt_have_platforms.append(platform)
            if platform in has_platforms and platform in doesnt_have_platforms:
                nonesense[0] = platform
        elif group == 1:
            genre, does_like_it, *_ = result
            if does_like_it:
                suitable_genres.append(genre)
            else:
                prohibited_genres.append(genre)
            if genre in suitable_genres and genre in prohibited_genres:
                nonesense[1] = genre
        elif group == 2:
            if wants_solo is not None:
                nonesense[2] = True
            wants_solo = not result[0]
    return (nonesense, has_platforms, doesnt_have_platforms, suitable_genres, prohibited_genres, wants_solo)


def facts_to_query(facts):
    (nonesense, has_platforms, doesnt_have_platforms, suitable_genres, prohibited_genres, wants_solo) = facts
    if nonesense != {}:
        print("Обнаружено противоречие. Пожалуйста, скорректируйте свой запрос.")
        return {}
    query = []
    if suitable_genres != []:
        query.append("("+";".join(["genre(X, " + g + ")" for g in suitable_genres])+")")
    else:
        query.append(
            "("+";".join(["genre(X, " + g + ")" for g in set(genres.values()) if g not in prohibited_genres])+")")
    if wants_solo is not None and wants_solo:
        query.append("is_open_world(X)")
    if wants_solo is not None and not wants_solo:
        query.append("has_multiplayer(X)")
    if has_platforms != []:
        query.append("("+";".join(["can_be_run_on(X, " + p.name + ")" for p in has_platforms])+")")
    else:
        query.append("can_be_run_on(X, Y), platform_worth_buying(Y)")

    query = ",".join(query)
    query = query.replace(",", ", ").replace(";", "; ")
    DEBUG("Запрос:\n" + query+".\n")
    result = query_prolog.query(query)
    results = {}
    for record in result:
        for key, value in record.items():
            k = results.get(key, [])
            if value not in k:
                results[key] = k + [value]
    return results
    # print(results)


def parse(text):
    print("-", text)
    semantics = split_based_on_semantics(text)
    facts = semantics_to_facts(semantics)
    result = facts_to_query(facts)
    if result == {} or result is None:
        print("Не найдено подходящих решений!\n\n\n")
        return False
    if len(result.keys()) == 2:
        if len(result['Y']) == 1:
            print("Рекоммендуется приобрести платформу: "+result['Y'][0])
        else:
            print("Рекоммендуется приобрести любую из следющих платформ: "+", ".join(result['Y']))

        if len(result['X']) == 1:
            print("И попробовать следующую игру: "+result['X'][0])
        else:
            print("И опробовать следующие игры: "+", ".join(result['X']))
    else:
        if len(result['X']) == 1:
            print("Рекоммендуется попробовать следующую игру: "+result['X'][0])
        else:
            print("Рекоммендуется ознакомиться со следующими играми: "+", ".join(result['X']))
    print("\n")
    return True


with open("file.pl", 'w') as file:
    for l in prolog_lines:
        file.write(l+".\n")

test_cases = [
    "У меня есть PS3. Я люблю выживание",
    "Я хочу поиграть с кем-то. Я купил плейстейшен 4",
    "Я играю на Нинтендо Свич. Мне нравятся квесты",
    "Я играю на Xbox. Мне не нравится жанр адвенчуры. Я хочу играть один",
    "У меня есть PC. У меня нет пк",
    "Я хочу поиграть в симулятор. Хочется поиграть онлайн",
]

for case in test_cases:
    parse(case)
