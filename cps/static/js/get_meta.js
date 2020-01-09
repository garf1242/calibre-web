/* This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
 *    Copyright (C) 2018  idalin<dalin.lin@gmail.com>
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program. If not, see <http://www.gnu.org/licenses/>.
 */
/*
 * Get Metadata from backend metadata providers
*/
/* global _, i18nMsg, tinymce, metadataProviders */ 

// store results in a { provider -> results } dictionary
var searchResults = {}

$(function () {
    var msg = i18nMsg;

    var templates = {
        bookResult: _.template(
            $("#template-book-result").html()
        )
    };

    function populateForm (book) {
        tinymce.get("description").setContent(book.description);
        var uniqueTags = [];
        $.each(book.tags, function(i, el) {
            if ($.inArray(el, uniqueTags) === -1) uniqueTags.push(el);
        });

        $("#bookAuthor").val(book.authors.join("&"));
        $("#book_title").val(book.title);
        $("#tags").val(uniqueTags.join(","));
        $("#rating").data("rating").setValue(Math.round(book.rating));
        $(".cover img").attr("src", book.cover);
        $("#cover_url").val(book.cover);
        $("#pubdate").val(book.publishedDate);
        $("#publisher").val(book.publisher)
        if (book.series != undefined) {
            $("#series").val(book.series)
        }
    }

    function showResult () {
        var allResultsEmpty = true;
        Object.values(searchResults).forEach(function(result) {
            if (result == null || result.length != 0) {
                allResultsEmpty = false;
            }
        });
        if (allResultsEmpty) {
            $("#meta-info").html("<p class=\"text-danger\">" + msg.no_result + "</p>");
            return;
		}
        if ($("#meta-info").text() == msg.loading) {
            // First showResult call, change loading message to list
            $("#meta-info").html("<ul id=\"book-list\" class=\"media-list\"></ul>");
        }
		Object.entries(searchResults).forEach(function([providerName, result]) {
            if (result == null) return;
			result.forEach(function(book) {
                var $book = $(templates.bookResult(book));
                $book.find("img").on("click", function () {
                    populateForm(book);
                });
                $("#book-list").append($book);
		    });
		});
    }

    function searchBook (providerName, bookId, keyword) {
	additionalKeywords = "";
	if (keyword) {
	    additionalKeywords = "?title=" + keyword;
	}
	delete searchResults[providerName];
        $.ajax({
            url: window.location.pathname + "/../../../ajax/metadata/"
		+ providerName + "/" + bookId + additionalKeywords,
            type: "GET",
            dataType: "json",
            jsonp: "callback",
            success: function success(data) {
                searchResults[providerName] = data;
            },
            error: function error() {
                $("#meta-info").html("<p class=\"text-danger\">" + msg.search_error + "!</p>"+ $("#meta-info")[0].innerHTML)
            },
            complete: function complete() {
                showResult();
            }
        });
    }

    function doSearch (bookId, keyword) {
        $("#meta-info").text(msg.loading);
        // Prepare results before launching every search
        searchResults = {}
        metadataProviders.forEach(function(provider) {
            if ( $("#show-" + provider.name).prop("checked") ) {
                searchResults[provider.name] = null;
            }
        });
        if (Object.keys(searchResults).length == 0) {
			showResult(); // no result
		} else {
            Object.keys(searchResults).forEach(function(providerName) {
                searchBook(providerName, bookId, keyword);
            });
		}
    }

    $("#meta-search").on("submit", function (e) {
        e.preventDefault();
        var bookId = $("#book_id").val();
        var keyword = $("#keyword").val();
	doSearch(bookId, keyword);
    });

    $("#get_meta").click(function () {
        var bookTitle = $("#book_title").val();
        var bookId = $("#book_id").val();
        $("#keyword").val(bookTitle);
        doSearch(bookId, bookTitle);
    });

});
