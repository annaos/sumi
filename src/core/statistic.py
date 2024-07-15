def create_header(delta):
    return "Статистика за последние %s часа\n" % (str(delta))


def create_statistic(messages):
    if len(messages) == 0:
        return "Никто ничего не написал."

    sorted_messages = {k: v for k, v in sorted(messages.items(), key=lambda x: x[1], reverse=True)}

    statistic = ""
    place = 1
    for user, count in sorted_messages.items():
        if place == 1:
            statistic +='\U0001F947'
        if place == 2:
            statistic +='\U0001F948'
        if place == 3:
            statistic +='\U0001F949'

        if place > 3 and count == 1:
            statistic +='\U0001F9D8'

        if count == 1:
            statistic += "%s: %d сообщение" % (user, count)
        else:
            statistic += "%s: %d сообщений" % (user, count)

        statistic +='\n'
        place += 1

    return statistic
